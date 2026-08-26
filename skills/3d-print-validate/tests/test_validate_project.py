from __future__ import annotations

import struct
import subprocess
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
VALIDATOR = ROOT / "scripts" / "validate_project.py"


def cube_triangles(x0=0.0, size=10.0):
    p = [
        (x0 + 0, 0, 0), (x0 + size, 0, 0), (x0 + size, size, 0), (x0 + 0, size, 0),
        (x0 + 0, 0, size), (x0 + size, 0, size), (x0 + size, size, size), (x0 + 0, size, size),
    ]
    faces = [
        (0, 2, 1), (0, 3, 2),
        (4, 5, 6), (4, 6, 7),
        (0, 1, 5), (0, 5, 4),
        (1, 2, 6), (1, 6, 5),
        (2, 3, 7), (2, 7, 6),
        (3, 0, 4), (3, 4, 7),
    ]
    return [(p[a], p[b], p[c]) for a, b, c in faces]


def write_binary_stl(path: Path, triangles):
    data = bytearray(80)
    data.extend(struct.pack("<I", len(triangles)))
    for a, b, c in triangles:
        data.extend(struct.pack("<12fH", 0, 0, 0, *a, *b, *c, 0))
    path.write_bytes(data)


def make_project(
    tmp_path: Path,
    triangles,
    *,
    expected_shells: int = 1,
    source: str | None = None,
    spec_update=None,
):
    (tmp_path / "docs").mkdir(exist_ok=True)
    (tmp_path / "src").mkdir(exist_ok=True)
    (tmp_path / "stl").mkdir(exist_ok=True)
    (tmp_path / "src/part.scad").write_text(
        source or "cube_size_mm = 10;\ncube([cube_size_mm, cube_size_mm, cube_size_mm]);\n"
    )
    write_binary_stl(tmp_path / "stl/part.stl", triangles)
    spec = {
        "schema_version": 1,
        "part": {"name": "part", "revision": "0.1.0", "product_class": "bracket", "purpose": "test"},
        "manufacturing": {
            "process": "fdm", "printer": "test", "build_volume_mm": [256, 256, 256],
            "material": "PETG", "nozzle_mm": 0.4, "layer_height_mm": 0.2,
        },
        "cad": {"backend": "openscad", "parametric": True, "units": "mm", "source_files": ["src/part.scad"]},
        "geometry": {
            "min_wall_mm": 1.6, "min_feature_mm": 1.6,
            "overlapping_solids_allowed": False,
            "stl_files": [{"path": "stl/part.stl", "body": "part", "expected_shells": expected_shells}],
        },
        "fit": {"required": False, "clearance_per_side_mm": 0.0, "evidence": "none"},
        "dimensions": [{
            "name": "cube size", "parameter": "cube_size_mm", "value_mm": 10,
            "tolerance_mm": 0.1, "source": "measured",
        }],
        "print": {
            "orientation": "base-on-bed", "bed_face": "bottom", "up_axis": "Z",
            "supports": "none", "max_overhang_deg": 45,
        },
        "service": {"environment": "dry", "drainage": "not-applicable"},
    }
    if spec_update:
        spec_update(spec)
    (tmp_path / "docs/PRINT_SPEC.yaml").write_text(yaml.safe_dump(spec, sort_keys=False))


def run(project: Path):
    return subprocess.run(
        [sys.executable, str(VALIDATOR), str(project)],
        text=True, capture_output=True, check=False,
    )


def test_valid_project_passes(tmp_path):
    make_project(tmp_path, cube_triangles())
    result = run(tmp_path)
    assert result.returncode == 0, result.stdout + result.stderr
    assert "RESULT: PASS" in result.stdout


def test_two_shells_declared_as_one_fail(tmp_path):
    make_project(tmp_path, cube_triangles() + cube_triangles(20.0))
    result = run(tmp_path)
    assert result.returncode == 1
    assert "expected 1, found 2" in result.stdout


def test_separated_shells_pass_when_declared(tmp_path):
    make_project(tmp_path, cube_triangles() + cube_triangles(20.0), expected_shells=2)
    result = run(tmp_path)
    assert result.returncode == 0, result.stdout + result.stderr


def test_overlapping_shells_fail_even_when_count_matches(tmp_path):
    make_project(tmp_path, cube_triangles() + cube_triangles(5.0), expected_shells=2)
    result = run(tmp_path)
    assert result.returncode == 1
    assert "G-overlap" in result.stdout


def test_inverted_volume_fails(tmp_path):
    inverted = [(a, c, b) for a, b, c in cube_triangles()]
    make_project(tmp_path, inverted)
    result = run(tmp_path)
    assert result.returncode == 1
    assert "G-volume" in result.stdout


def test_exact_build_envelope_fails(tmp_path):
    make_project(tmp_path, cube_triangles(size=256))
    result = run(tmp_path)
    assert result.returncode == 1
    assert "G-build-volume" in result.stdout


def test_datasheet_required_fit_passes(tmp_path):
    (tmp_path / "fit").mkdir()
    (tmp_path / "fit/coupon.stl").write_bytes(b"coupon")

    def update(spec):
        spec["fit"] = {
            "required": True,
            "clearance_per_side_mm": 0.4,
            "evidence": "datasheet",
            "coupon": "fit/coupon.stl",
        }

    make_project(tmp_path, cube_triangles(), spec_update=update)
    result = run(tmp_path)
    assert result.returncode == 0, result.stdout + result.stderr


def test_wet_slots_drainage_passes(tmp_path):
    def update(spec):
        spec["service"] = {"environment": "wet", "drainage": "slots"}
        spec["manufacturing"]["material"] = "PETG"

    make_project(tmp_path, cube_triangles(), spec_update=update)
    result = run(tmp_path)
    assert result.returncode == 0, result.stdout + result.stderr


def test_parameter_substring_is_not_a_declaration(tmp_path):
    make_project(
        tmp_path,
        cube_triangles(),
        source="outer_width = 10;\n// width = 1;\n",
        spec_update=lambda spec: spec["dimensions"].__setitem__(
            0,
            {
                "name": "width",
                "parameter": "width",
                "value_mm": 10,
                "tolerance_mm": 0.1,
                "source": "measured",
            },
        ),
    )
    result = run(tmp_path)
    assert result.returncode == 1
    assert "CAD parameter not found" in result.stdout
