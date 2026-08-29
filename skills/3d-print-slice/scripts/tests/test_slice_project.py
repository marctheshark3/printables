from __future__ import annotations

import json
import os
import struct
import subprocess
import sys
from pathlib import Path

import yaml

SCRIPTS = Path(__file__).resolve().parents[1]
SLICE = SCRIPTS / "slice_project.py"


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


def make_project(tmp_path: Path) -> Path:
    (tmp_path / "docs").mkdir()
    (tmp_path / "src").mkdir()
    (tmp_path / "stl").mkdir()
    (tmp_path / "src" / "part.scad").write_text(
        "cube_size_mm = 10;\ncube([cube_size_mm, cube_size_mm, cube_size_mm]);\n"
    )
    write_binary_stl(tmp_path / "stl" / "part.stl", box_triangles())
    spec = {
        "schema_version": 1,
        "part": {"name": "slice-coupon", "revision": "0.1.0", "product_class": "bracket", "purpose": "slice test"},
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
        "fit": {"required": False, "clearance_per_side_mm": 0.0, "evidence": "none"},
        "dimensions": [{
            "name": "cube size", "parameter": "cube_size_mm", "value_mm": 10,
            "tolerance_mm": 0.1, "source": "measured",
        }],
        "print": {
            "orientation": "base-on-bed", "bed_face": "bottom", "up_axis": "Z",
            "supports": "build-plate-only", "max_overhang_deg": 50,
        },
        "service": {"environment": "dry", "drainage": "not-applicable"},
    }
    (tmp_path / "docs" / "PRINT_SPEC.yaml").write_text(
        yaml.safe_dump(spec, sort_keys=False), encoding="utf-8"
    )
    return tmp_path


def run_slice(project: Path, env=None):
    merged = os.environ.copy()
    for key in ("ORCA_SLICER", "BAMBU_STUDIO", "PRUSA_SLICER"):
        merged.pop(key, None)
    if env:
        merged.update(env)
    return subprocess.run(
        [sys.executable, str(SLICE), str(project)],
        text=True,
        capture_output=True,
        check=False,
        env=merged,
    )


def _assert_card(project: Path):
    path = project / "slice" / "bracket.process.json"
    assert path.is_file()
    card = json.loads(path.read_text(encoding="utf-8"))
    assert card["printer"] == "bambu-lab-p1s"
    assert card["build_volume_mm"] == [256, 256, 256]
    assert card["nozzle_mm"] == 0.4
    assert card["layer_height_mm"] == 0.2
    assert card["material"] == "PETG"
    assert card["bed_face"] == "bottom"
    assert card["up_axis"] == "Z"
    assert card["orientation"] == "base-on-bed"
    assert card["supports"] == "build-plate-only"
    assert card["max_overhang_deg"] == 50
    assert card["stl"] == "stl/part.stl"
    assert card["body"] == "bracket"
    assert not list(project.joinpath("slice").glob("*.3mf"))


def test_process_card_without_slicer_skips_3mf(tmp_path):
    project = make_project(tmp_path)
    first = run_slice(project)
    assert first.returncode == 0, first.stdout + first.stderr
    assert "SKIP: no slicer CLI" in first.stdout
    _assert_card(project)
    second = run_slice(project)
    assert second.returncode == 0, second.stdout + second.stderr
    assert "SKIP: no slicer CLI" in second.stdout
    _assert_card(project)


def test_slicer_env_does_not_write_renamed_stl(tmp_path):
    project = make_project(tmp_path)
    fake = tmp_path / "not-a-slicer"
    fake.write_text("#!/bin/sh\nexit 1\n")
    fake.chmod(0o755)
    result = run_slice(project, env={"ORCA_SLICER": str(fake)})
    assert result.returncode == 0, result.stdout + result.stderr
    assert not list(project.joinpath("slice").glob("*.3mf"))
    assert (project / "slice" / "bracket.process.json").is_file()
