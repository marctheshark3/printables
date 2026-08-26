from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
SCRIPT = ROOT / "skills" / "3d-print-sim" / "scripts" / "roll_table_flat.py"
BRIEF = ROOT / "skills" / "3d-print-design-brief" / "scripts"
SIM = ROOT / "skills" / "3d-print-sim" / "scripts"
ROVER = ROOT / "examples" / "robot-kit-01-rover"
for path in (str(BRIEF), str(SIM)):
    if path not in sys.path:
        sys.path.insert(0, path)


def test_always_on_tests_do_not_import_mujoco():
    assert "mujoco" not in sys.modules


def test_roll_table_flat_skips_without_mujoco():
    import importlib.util

    result = subprocess.run(
        [sys.executable, str(SCRIPT), str(ROVER)],
        text=True,
        capture_output=True,
        check=False,
    )
    if importlib.util.find_spec("mujoco") is None:
        assert result.returncode == 0, result.stdout + result.stderr
        assert "SKIP" in result.stdout
        assert "mujoco not installed" in result.stdout
        return
    assert result.returncode in {0, 1}
    assert "RESULT:" in result.stdout or "SKIP" in result.stdout


def test_roll_script_has_no_module_level_mujoco_import():
    text = SCRIPT.read_text(encoding="utf-8")
    assert "import mujoco" not in text.split("def run_roll")[0]
    assert "from mujoco" not in text.split("def run_roll")[0]


def test_roll_model_errors_fail_closed_without_inventing_numbers():
    from print_spec import load_spec
    from roll_table_flat import roll_model_errors

    spec, errors = load_spec(
        ROVER / "docs/PRINT_SPEC.yaml", project=ROVER, check_files=False
    )
    assert spec is not None and errors == []
    assert roll_model_errors(spec) == []

    from dataclasses import replace

    empty = replace(spec, calibration=(), dimensions=spec.dimensions[:1], sim_scene=None)
    hard = roll_model_errors(empty)
    assert any("mass calibration" in item for item in hard)
    assert any("friction calibration" in item for item in hard)
    assert any("sim.scene" in item for item in hard)
    assert any("wheel_od_mm" in item for item in hard)
