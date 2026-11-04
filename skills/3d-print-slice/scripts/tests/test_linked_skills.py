"""The shared workflow must work when each package is a directory symlink."""
import importlib.util
import os
from pathlib import Path
import shutil
import subprocess
import sys

import pytest

REPO = Path(__file__).resolve().parents[4]


@pytest.fixture
def linked_skills(tmp_path):
    discovery = tmp_path / "skills"
    discovery.mkdir()
    for name in ("3d-print-design-brief", "3d-print-validate", "3d-print-multi-material",
                 "3d-print-slice", "3d-print-pack", "3d-print-blender"):
        stored = tmp_path / "versions" / name / "revision"
        shutil.copytree(REPO / "skills" / name, stored, ignore=shutil.ignore_patterns("__pycache__"))
        (discovery / name).symlink_to(stored, target_is_directory=True)
    return discovery


@pytest.mark.parametrize("example", ["two-color-enclosure-lid", "bracket-coupon-vibecad"])
def test_linked_validation_slice_and_pack(tmp_path, linked_skills, example):
    project = tmp_path / "project"
    shutil.copytree(REPO / "examples" / example, project)
    commands = [("3d-print-validate", "validate_project.py"),
                ("3d-print-slice", "slice_project.py"), ("3d-print-pack", "pack_project.py")]
    if example == "two-color-enclosure-lid":
        commands.insert(1, ("3d-print-multi-material", "material_project.py"))
    env = {key: value for key, value in os.environ.items() if key not in
           ("PYTHONPATH", "BAMBU_STUDIO", "ORCA_SLICER", "PRUSA_SLICER")}
    for skill, script in commands:
        args = [sys.executable, str(linked_skills / skill / "scripts" / script)]
        if script == "material_project.py":
            args.append("plan")
        result = subprocess.run([*args, str(project)], cwd=tmp_path, env=env, capture_output=True, text=True)
        assert result.returncode == 0, result.stdout + result.stderr
    assert list((project / "pack").glob("*.zip"))


def test_linked_assembly_validation(tmp_path, linked_skills):
    project = tmp_path / "rover"
    shutil.copytree(REPO / "examples/robot-kit-01-rover", project)
    result = subprocess.run([sys.executable, str(linked_skills / "3d-print-validate/scripts/validate_assembly.py"),
                             str(project)], cwd=tmp_path, capture_output=True, text=True)
    assert result.returncode == 0, result.stdout + result.stderr


def test_linked_blender_finds_the_shared_validator(linked_skills, monkeypatch):
    for key in ("PRINT_VALIDATOR", "DFM_GATE"):
        monkeypatch.delenv(key, raising=False)
    path = linked_skills / "3d-print-blender/scripts/pblend_cli.py"
    spec = importlib.util.spec_from_file_location("linked_blender_cli", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    assert module.find_project_validator() == linked_skills / "3d-print-validate/scripts/validate_project.py"
