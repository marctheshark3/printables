from __future__ import annotations

import hashlib
import struct
import subprocess
import sys
import zipfile
from pathlib import Path

import yaml

SCRIPTS = Path(__file__).resolve().parents[1]
PACK = SCRIPTS / "pack_project.py"


def box_triangles(sx=10.0, sy=10.0, sz=10.0):
    p = [
        (0, 0, 0), (sx, 0, 0), (sx, sy, 0), (0, sy, 0),
        (0, 0, sz), (sx, 0, sz), (sx, sy, sz), (0, sy, sz),
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


def write_binary_stl(path: Path, triangles) -> None:
    data = bytearray(80)
    data.extend(struct.pack("<I", len(triangles)))
    for a, b, c in triangles:
        data.extend(struct.pack("<12fH", 0, 0, 0, *a, *b, *c, 0))
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(data)


def spec_dict():
    return {
        "schema_version": 1,
        "part": {"name": "coupon-pack", "revision": "0.1.0", "product_class": "bracket", "purpose": "pack test"},
        "manufacturing": {
            "process": "fdm", "printer": "bambu-lab-p1s", "build_volume_mm": [256, 256, 256],
            "material": "PETG", "nozzle_mm": 0.4, "layer_height_mm": 0.2,
        },
        "cad": {"backend": "openscad", "parametric": True, "units": "mm", "source_files": ["src/part.scad"]},
        "geometry": {
            "min_wall_mm": 1.6, "min_feature_mm": 1.6,
            "overlapping_solids_allowed": False,
            "stl_files": [{"path": "stl/part.stl", "body": "part", "expected_shells": 1}],
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


def make_gated(tmp_path: Path, triangles=None) -> Path:
    (tmp_path / "docs").mkdir()
    (tmp_path / "src").mkdir()
    (tmp_path / "stl").mkdir()
    (tmp_path / "src" / "part.scad").write_text(
        "cube_size_mm = 10;\ncube([cube_size_mm, cube_size_mm, cube_size_mm]);\n"
    )
    write_binary_stl(tmp_path / "stl" / "part.stl", triangles or box_triangles())
    (tmp_path / "docs" / "PRINT_SPEC.yaml").write_text(
        yaml.safe_dump(spec_dict(), sort_keys=False), encoding="utf-8"
    )
    (tmp_path / "renders").mkdir()
    (tmp_path / "renders" / "still.png").write_bytes(b"\x89PNG\r\n\x1a\n")
    (tmp_path / "step").mkdir()
    (tmp_path / "step" / "part.step").write_text("ISO-10303-21;\n")
    return tmp_path


def run_pack(project: Path, extra=None):
    argv = [sys.executable, str(PACK), str(project)]
    if extra:
        argv.extend(extra)
    return subprocess.run(argv, text=True, capture_output=True, check=False)


def _assert_zip_contents(project: Path) -> zipfile.ZipFile:
    zpath = project / "pack" / "coupon-pack.zip"
    assert zpath.is_file(), zpath
    zf = zipfile.ZipFile(zpath)
    names = set(zf.namelist())
    assert "docs/PRINT_SPEC.yaml" in names
    assert "src/part.scad" in names
    assert "stl/part.stl" in names
    assert "docs/PRINT_NOTES.md" in names
    assert "MANIFEST.sha256" in names
    assert "renders/still.png" in names
    assert "step/part.step" in names
    assert not any(Path(name).is_absolute() for name in names)
    notes = zf.read("docs/PRINT_NOTES.md").decode("utf-8")
    for needle in (
        "orientation: base-on-bed",
        "bed_face: bottom",
        "supports: none",
        "material: PETG",
        "nozzle_mm: 0.4",
        "layer_height_mm: 0.2",
    ):
        assert needle in notes, needle
    manifest = zf.read("MANIFEST.sha256").decode("utf-8")
    for line in manifest.strip().splitlines():
        digest, rel = line.split("  ", 1)
        assert hashlib.sha256(zf.read(rel)).hexdigest() == digest
        assert rel != "MANIFEST.sha256"
    return zf


def test_pack_zip_contains_spec_stl_notes_manifest(tmp_path):
    project = make_gated(tmp_path)
    first = run_pack(project)
    assert first.returncode == 0, first.stdout + first.stderr
    _assert_zip_contents(project)
    second = run_pack(project)
    assert second.returncode == 0, second.stdout + second.stderr
    _assert_zip_contents(project)


def test_pack_refuses_ungated_project(tmp_path):
    inverted = [(a, c, b) for a, b, c in box_triangles()]
    project = make_gated(tmp_path, triangles=inverted)
    result = run_pack(project)
    assert result.returncode != 0
    assert "refusing to pack" in result.stdout or "RESULT: FAIL" in result.stdout
    zpath = project / "pack" / "coupon-pack.zip"
    assert not zpath.exists()
