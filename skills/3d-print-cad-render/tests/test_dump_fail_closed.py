"""Host python must not invent a scene. FreeCADCmd is required for a real dump."""
from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DUMP = ROOT / "scripts" / "dump_cad_scene.py"
BOX = ROOT / "scripts" / "mill_box_step.py"


def _run(script: Path, env: dict) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(script)],
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )


def _env() -> dict:
    env = os.environ.copy()
    for key in ("CAD_RENDER_STEP", "CAD_RENDER_OUT", "FREECAD_CMD", "VIBECAD_CMD"):
        env.pop(key, None)
    return env


def test_dump_requires_step_and_out():
    proc = _run(DUMP, _env())
    assert proc.returncode == 1
    assert "CAD_RENDER_STEP and CAD_RENDER_OUT are required" in proc.stderr


def test_dump_refuses_missing_step(tmp_path):
    env = _env()
    env["CAD_RENDER_STEP"] = str(tmp_path / "missing.step")
    env["CAD_RENDER_OUT"] = str(tmp_path / "scene.json")
    proc = _run(DUMP, env)
    assert proc.returncode == 1
    assert "STEP not found" in proc.stderr
    assert not (tmp_path / "scene.json").exists()


def test_host_python_does_not_write_a_fake_scene(tmp_path):
    step = tmp_path / "box.step"
    step.write_text("ISO-10303-21;\n", encoding="utf-8")
    out = tmp_path / "scene.json"
    env = _env()
    env["CAD_RENDER_STEP"] = str(step)
    env["CAD_RENDER_OUT"] = str(out)
    proc = _run(DUMP, env)
    assert proc.returncode == 1
    assert "FreeCAD Part missing" in proc.stderr
    assert not out.exists()


def test_mill_box_requires_out_path():
    proc = _run(BOX, _env())
    assert proc.returncode == 1
    assert "CAD_RENDER_STEP required" in proc.stderr
