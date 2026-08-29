from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import yaml

SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
GENERATE = SCRIPTS / "generate_coupon.py"
RECORD = SCRIPTS / "record_fit.py"
OPENSCAD = Path(__file__).resolve().parents[2] / "3d-print-openscad"
VALIDATE = Path(__file__).resolve().parents[2] / "3d-print-validate" / "scripts"
sys.path.insert(0, str(VALIDATE))
from stl_io import bbox_and_volume, load_binary_stl  # noqa: E402


def spec_dict():
    return {
        "schema_version": 1,
        "part": {"name": "bracket", "revision": "0.1.0", "product_class": "bracket", "purpose": "fit coupon"},
        "manufacturing": {
            "process": "fdm", "printer": "bambu-lab-p1s", "build_volume_mm": [256, 256, 256],
            "material": "PETG", "nozzle_mm": 0.4, "layer_height_mm": 0.2,
        },
        "cad": {"backend": "openscad", "parametric": True, "units": "mm", "source_files": ["src/part.scad"]},
        "geometry": {
            "min_wall_mm": 1.6, "min_feature_mm": 1.6,
            "overlapping_solids_allowed": False,
            "stl_files": [{"path": "stl/part.stl", "body": "bracket", "expected_shells": 1}],
        },
        "fit": {
            "required": True,
            "clearance_per_side_mm": 0.4,
            "evidence": "datasheet",
            "coupon": "fit/bracket-coupon.stl",
        },
        "dimensions": [
            {
                "name": "hole_d", "parameter": "hole_d", "value_mm": 4.2,
                "tolerance_mm": 0.1, "source": "datasheet",
            },
            {
                "name": "object_x", "parameter": "object_x", "value_mm": 40.0,
                "tolerance_mm": 0.2, "source": "measured",
            },
        ],
        "print": {
            "orientation": "base-on-bed", "bed_face": "bottom", "up_axis": "Z",
            "supports": "none", "max_overhang_deg": 45,
        },
        "service": {"environment": "dry", "drainage": "not-applicable"},
    }


def make_project(tmp_path: Path) -> Path:
    (tmp_path / "docs").mkdir(parents=True)
    (tmp_path / "src").mkdir(parents=True)
    (tmp_path / "stl").mkdir(parents=True)
    (tmp_path / "src" / "part.scad").write_text("hole_d = 4.2;\nobject_x = 40;\n")
    (tmp_path / "stl" / "part.stl").write_bytes(b"solid")
    (tmp_path / "docs" / "PRINT_SPEC.yaml").write_text(
        yaml.safe_dump(spec_dict(), sort_keys=False), encoding="utf-8"
    )
    return tmp_path


def test_coupon_generator_parameter_names_match_spec(tmp_path):
    project = make_project(tmp_path)
    result = subprocess.run(
        [sys.executable, str(GENERATE), str(project)],
        text=True,
        capture_output=True,
        check=False,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    scad = (project / "fit" / "bracket-coupon.scad").read_text(encoding="utf-8")
    assert "hole_d = 4.2;" in scad
    assert "object_x = 40.0;" in scad or "object_x = 40;" in scad
    assert "clearance_per_side_mm = 0.4;" in scad
    stl = project / "fit" / "bracket-coupon.stl"
    assert stl.is_file()
    assert stl.stat().st_size >= 84
    audited = subprocess.run(
        [
            sys.executable,
            str(VALIDATE / "validate_stl.py"),
            "--stl",
            str(stl),
            "--build-x-mm",
            "256",
            "--build-y-mm",
            "256",
            "--build-z-mm",
            "256",
            "--expected-components",
            "1",
            "--min-wall-mm",
            "1.6",
            "--min-feature-mm",
            "1.6",
        ],
        text=True,
        capture_output=True,
        check=False,
    )
    assert audited.returncode == 0, audited.stdout + audited.stderr
    assert "components=1" in audited.stdout
    _normals, tris, ntri = load_binary_stl(stl)
    _mn, _mx, vol = bbox_and_volume(tris)
    solid = 20.0 * 20.0 * 3.2
    assert ntri > 12
    assert vol < solid * 0.98


def test_coupon_stl_hole_tracks_named_hole_d(tmp_path):
    p_small = make_project(tmp_path / "small")
    p_large = make_project(tmp_path / "large")
    spec = yaml.safe_load((p_large / "docs" / "PRINT_SPEC.yaml").read_text(encoding="utf-8"))
    spec["dimensions"][0]["value_mm"] = 8.0
    (p_large / "src" / "part.scad").write_text("hole_d = 8.0;\nobject_x = 40;\n")
    (p_large / "docs" / "PRINT_SPEC.yaml").write_text(
        yaml.safe_dump(spec, sort_keys=False), encoding="utf-8"
    )
    for project in (p_small, p_large):
        result = subprocess.run(
            [sys.executable, str(GENERATE), str(project)],
            text=True,
            capture_output=True,
            check=False,
        )
        assert result.returncode == 0, result.stdout + result.stderr
    small = p_small / "fit" / "bracket-coupon.stl"
    large = p_large / "fit" / "bracket-coupon.stl"
    assert small.read_bytes() != large.read_bytes()
    _n1, t1, n1 = load_binary_stl(small)
    _n2, t2, n2 = load_binary_stl(large)
    _mn, _mx, v_small = bbox_and_volume(t1)
    _mn, _mx, v_large = bbox_and_volume(t2)
    solid = 20.0 * 20.0 * 3.2
    assert v_small < solid
    assert v_large < v_small
    assert n1 > 12 and n2 > 12


def test_record_fit_writes_measured_value(tmp_path):
    project = make_project(tmp_path)
    result = subprocess.run(
        [
            sys.executable, str(RECORD), str(project),
            "--parameter", "hole_d", "--measured-mm", "4.15",
        ],
        text=True,
        capture_output=True,
        check=False,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    data = yaml.safe_load((project / "docs" / "PRINT_SPEC.yaml").read_text(encoding="utf-8"))
    dim = next(item for item in data["dimensions"] if item["parameter"] == "hole_d")
    assert dim["source"] == "fit-tested"
    assert float(dim["value_mm"]) == 4.15
    assert float(data["fit"]["measured_mm"]["hole_d"]) == 4.15


def test_record_fit_without_measured_mm_does_not_write(tmp_path):
    project = make_project(tmp_path)
    before = (project / "docs" / "PRINT_SPEC.yaml").read_text(encoding="utf-8")
    result = subprocess.run(
        [sys.executable, str(RECORD), str(project), "--parameter", "hole_d"],
        text=True,
        capture_output=True,
        check=False,
    )
    assert result.returncode != 0
    assert "will not invent" in result.stdout
    after = (project / "docs" / "PRINT_SPEC.yaml").read_text(encoding="utf-8")
    assert after == before


def test_heat_set_reference_and_templates_exist():
    ref = (OPENSCAD / "references" / "heat-set-inserts-fdm.md").read_text(encoding="utf-8")
    for needle in ("M2", "M3", "M4", "datasheet", "CNC Kitchen"):
        assert needle in ref
    boss = (OPENSCAD / "templates" / "insert_boss.scad").read_text(encoding="utf-8")
    coupon = (OPENSCAD / "templates" / "insert_coupon.scad").read_text(encoding="utf-8")
    thread = (OPENSCAD / "templates" / "printed_thread.scad").read_text(encoding="utf-8")
    assert "insert_od_mm" in boss and "insert_hole_d_mm" in boss
    assert "insert_od_mm" in coupon
    assert "opt-in" in thread.lower()
    assert "printed_thread = false" in thread
