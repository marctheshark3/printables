from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

import pytest

SCRIPTS = Path(__file__).resolve().parents[1]
PREVERSE = SCRIPTS / "preverse_cli.py"

from mesh_fixtures import cube_tris, write_ascii_cube  # noqa: E402
from stl_write import write_binary_stl  # noqa: E402


def test_cli_import_does_not_load_occ():
    assert "cadquery" not in sys.modules
    assert "FreeCAD" not in sys.modules
    import preverse_cli  # noqa: F401

    assert "cadquery" not in sys.modules
    assert "FreeCAD" not in sys.modules


def test_cli_version():
    result = subprocess.run(
        [sys.executable, str(PREVERSE), "version"],
        text=True,
        capture_output=True,
        check=False,
    )
    assert result.returncode == 0
    assert "preverse" in result.stdout


def test_analyze_missing_stl_exits_2(tmp_path: Path):
    result = subprocess.run(
        [sys.executable, str(PREVERSE), "analyze", "--project", str(tmp_path), "--body", "cube"],
        text=True,
        capture_output=True,
        check=False,
    )
    assert result.returncode == 2


def test_run_missing_kernel_keeps_parametric_ir(tmp_path: Path):
    stl = tmp_path / "cube.stl"
    write_binary_stl(stl, cube_tris(20.0))
    env = os.environ.copy()
    env.pop("VIBECAD_CMD", None)
    env.pop("PREVERSE_STEP_IMAGE", None)
    env.pop("PREVERSE_PYTHON", None)
    result = subprocess.run(
        [
            sys.executable,
            str(PREVERSE),
            "run",
            "--stl",
            str(stl),
            "--project",
            str(tmp_path),
            "--body",
            "cube",
        ],
        text=True,
        capture_output=True,
        check=False,
        env=env,
    )
    assert result.returncode == 2, result.stderr + result.stdout
    ir_path = tmp_path / "reverse" / "cube.ir.json"
    assert ir_path.is_file()
    import json

    ir = json.loads(ir_path.read_text(encoding="utf-8"))
    assert ir["class"] == "parametric"
    assert any(f.get("type") == "extrude" for f in ir.get("features") or [])
    assert not (tmp_path / "step" / "cube.step").exists()


def test_coupon_export_missing_kernel_exit_2():
    project = Path(__file__).resolve().parents[4] / "examples" / "bracket-coupon-reverse"
    env = os.environ.copy()
    env.pop("VIBECAD_CMD", None)
    env.pop("PREVERSE_STEP_IMAGE", None)
    env.pop("PREVERSE_PYTHON", None)
    result = subprocess.run(
        [
            sys.executable,
            str(PREVERSE),
            "export",
            "--project",
            str(project),
            "--body",
            "bracket",
        ],
        text=True,
        capture_output=True,
        check=False,
        env=env,
    )
    assert result.returncode == 2, result.stderr + result.stdout
    assert not (project / "step" / "bracket.step").exists()


def test_export_and_run_missing_kernel_exit_2(tmp_path: Path):
    stl = tmp_path / "cube.stl"
    write_binary_stl(stl, cube_tris(20.0))
    env = os.environ.copy()
    env.pop("VIBECAD_CMD", None)
    env.pop("PREVERSE_STEP_IMAGE", None)
    env.pop("PREVERSE_PYTHON", None)
    for cmd in ("export", "run"):
        result = subprocess.run(
            [
                sys.executable,
                str(PREVERSE),
                cmd,
                "--stl",
                str(stl),
                "--project",
                str(tmp_path),
                "--body",
                "cube",
            ],
            text=True,
            capture_output=True,
            check=False,
            env=env,
        )
        assert result.returncode == 2, result.stderr + result.stdout
        assert not (tmp_path / "step").exists() or not any((tmp_path / "step").glob("*.step"))


def test_pipeline_commands_on_cube(tmp_path: Path):
    stl = tmp_path / "cube.stl"
    write_binary_stl(stl, cube_tris(20.0))
    for cmd in ("analyze", "segment", "sketch", "features", "spec", "rebuild", "compare"):
        result = subprocess.run(
            [sys.executable, str(PREVERSE), cmd, "--stl", str(stl), "--project", str(tmp_path), "--body", "cube"],
            text=True,
            capture_output=True,
            check=False,
        )
        assert result.returncode == 0, f"{cmd}: {result.stderr}\n{result.stdout}"
    assert (tmp_path / "reverse" / "cube.ir.json").is_file()
    assert (tmp_path / "docs" / "PRINT_SPEC.yaml").is_file()
    assert (tmp_path / "src" / "cube.py").is_file()
    assert (tmp_path / "reports" / "cube.deviation.json").is_file()
    src = (tmp_path / "src" / "cube.py").read_text(encoding="utf-8")
    assert "width_mm =" in src
    gate = subprocess.run(
        [sys.executable, str(PREVERSE), "gate", "--stl", str(stl), "--project", str(tmp_path), "--body", "cube"],
        text=True,
        capture_output=True,
        check=False,
    )
    assert gate.returncode == 0, gate.stderr + gate.stdout
    src = (tmp_path / "src" / "cube.py").read_text(encoding="utf-8")
    assert "box(width_mm, depth_mm, height_mm)" not in src
    assert "write_ir_stl" not in Path(PREVERSE).read_text(encoding="utf-8")


def test_compare_uses_existing_rebuilt_stl(tmp_path: Path):
    stl = tmp_path / "cube.stl"
    write_binary_stl(stl, cube_tris(20.0))
    for cmd in ("analyze", "segment", "sketch", "features", "compare"):
        result = subprocess.run(
            [sys.executable, str(PREVERSE), cmd, "--stl", str(stl), "--project", str(tmp_path), "--body", "cube"],
            text=True,
            capture_output=True,
            check=False,
        )
        assert result.returncode == 0, f"{cmd}: {result.stderr}\n{result.stdout}"
    # Replace the rebuilt STL with a different solid. Compare must use that file.
    write_binary_stl(tmp_path / "stl" / "cube.stl", cube_tris(10.0))
    result = subprocess.run(
        [sys.executable, str(PREVERSE), "compare", "--stl", str(stl), "--project", str(tmp_path), "--body", "cube"],
        text=True,
        capture_output=True,
        check=False,
    )
    assert result.returncode == 1, result.stdout + result.stderr
    assert "deviation exceeds" in result.stderr or "deviation exceeds" in result.stdout


def test_analyze_dispatch_writes_ir(tmp_path: Path):
    stl = tmp_path / "cube.stl"
    write_ascii_cube(stl, 20.0)
    result = subprocess.run(
        [
            sys.executable,
            str(PREVERSE),
            "analyze",
            "--stl",
            str(stl),
            "--project",
            str(tmp_path),
            "--body",
            "cube",
        ],
        text=True,
        capture_output=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr + result.stdout
    ir = tmp_path / "reverse" / "cube.ir.json"
    assert ir.is_file()
    text = ir.read_text(encoding="utf-8")
    assert '"units": "mm"' in text
    assert '"schema_version": 1' in text
