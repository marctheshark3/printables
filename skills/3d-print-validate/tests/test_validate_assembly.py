from __future__ import annotations

import struct
import subprocess
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
VALIDATOR = ROOT / "scripts" / "validate_assembly.py"
SCRIPTS = ROOT / "scripts"
BRIEF = ROOT.parent / "3d-print-design-brief" / "scripts"
sys.path.insert(0, str(SCRIPTS))
sys.path.insert(0, str(BRIEF))

from assembly import (  # noqa: E402
    ALLOWABLE_SHEAR_MPA,
    hub_shear_mpa,
    l1_occupancy,
    l2_sweep,
    l3_loads,
    moment_to_n_m,
    place_assembly,
    rpy_matrix,
    transform_tris,
)
from print_spec import parse_spec  # noqa: E402


def cube_triangles(x0=0.0, y0=0.0, z0=0.0, sx=10.0, sy=10.0, sz=10.0):
    p = [
        (x0, y0, z0), (x0 + sx, y0, z0), (x0 + sx, y0 + sy, z0), (x0, y0 + sy, z0),
        (x0, y0, z0 + sz), (x0 + sx, y0, z0 + sz), (x0 + sx, y0 + sy, z0 + sz), (x0, y0 + sy, z0 + sz),
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


def pose(xyz, rpy=(0.0, 0.0, 0.0)):
    return {"xyz_mm": list(xyz), "rpy_deg": list(rpy)}


def base_spec():
    return {
        "schema_version": 1,
        "part": {"name": "kit", "revision": "0.1.0", "product_class": "robot-module", "purpose": "test"},
        "manufacturing": {
            "process": "fdm", "printer": "test", "build_volume_mm": [256, 256, 256],
            "material": "PETG", "nozzle_mm": 0.4, "layer_height_mm": 0.2,
        },
        "cad": {"backend": "openscad", "parametric": True, "units": "mm", "source_files": ["src/part.scad"]},
        "geometry": {
            "min_wall_mm": 1.6, "min_feature_mm": 1.6,
            "overlapping_solids_allowed": False,
            "stl_files": [
                {"path": "stl/chassis.stl", "body": "chassis", "expected_shells": 1},
                {"path": "stl/wheel.stl", "body": "wheel", "expected_shells": 1},
            ],
        },
        "fit": {"required": False, "clearance_per_side_mm": 0.0, "evidence": "none"},
        "dimensions": [
            {"name": "cube size", "parameter": "cube_size_mm", "value_mm": 10, "tolerance_mm": 0.1, "source": "measured"},
            {"name": "hub_od", "parameter": "hub_od_mm", "value_mm": 12.0, "tolerance_mm": 0.2, "source": "from-user"},
            {"name": "wheel_bore", "parameter": "wheel_bore_d_mm", "value_mm": 3.3, "tolerance_mm": 0.1, "source": "datasheet"},
        ],
        "print": {
            "orientation": "base-on-bed", "bed_face": "bottom", "up_axis": "Z",
            "supports": "none", "max_overhang_deg": 45,
        },
        "service": {"environment": "dry", "drainage": "not-applicable"},
        "hardware": {
            "components": [
                {
                    "id": "mcu",
                    "mpn_or_generic": "ESP32-C3 Super Mini",
                    "role": "mcu",
                    "qty": 1,
                    "envelope_mm": [8.0, 8.0, 4.0],
                    "interfaces": [
                        {
                            "name": "mcu_length",
                            "parameter": "mcu_length_mm",
                            "value_mm": 8.0,
                            "tolerance_mm": 0.2,
                            "source": "datasheet",
                        }
                    ],
                }
            ]
        },
    }


def assembly_block(
    wheel_xyz,
    wheel_rpy=(0.0, 0.0, 0.0),
    clearance=0.2,
    limits=True,
    stall_source="datasheet",
    axis=(1.0, 0.0, 0.0),
):
    joints = [
        {
            "id": "wheel_left",
            "type": "revolute",
            "parent": "chassis",
            "child": "wheel_left",
            "axis": list(axis),
            "clearance_per_side_mm": clearance,
            "source": "datasheet",
        }
    ]
    if limits:
        joints[0]["limits"] = {"min_deg": 0, "max_deg": 360}
    return {
        "assembly": {
            "frame": "assembled",
            "bodies": [
                {"id": "chassis", "body": "chassis", "parent": "world", "pose": pose((0, 0, 0))},
                {"id": "wheel_left", "body": "wheel", "parent": "chassis", "pose": pose(wheel_xyz, wheel_rpy)},
                {"id": "mcu", "hardware": "mcu", "parent": "chassis", "pose": pose((80, 80, 0))},
            ],
            "joints": joints,
        },
        "loads": [
            {
                "id": "gravity",
                "kind": "gravity",
                "target": "assembled",
                "magnitude": 9810,
                "units": "mm_s2",
                "safety_factor": 2.0,
                "source": "from-user",
            },
            {
                "id": "stall_left",
                "kind": "moment",
                "target": "wheel_left",
                "magnitude": 0.049,
                "units": "N_m",
                "safety_factor": 2.0,
                "source": stall_source,
                "section": {"outer_parameter": "hub_od_mm", "inner_parameter": "wheel_bore_d_mm"},
            },
        ],
        "sim": {
            "scene": {
                "id": "table-flat",
                "gravity_mm_s2": [0, 0, -9810],
                "floor": {"z_mm": 0},
                "friction": {"mu": 0.6, "source": "from-user"},
            }
        },
    }


def make_kit(tmp_path: Path, wheel_xyz, *, chassis=None, wheel=None, **assembly_kw):
    (tmp_path / "docs").mkdir(exist_ok=True)
    (tmp_path / "src").mkdir(exist_ok=True)
    (tmp_path / "stl").mkdir(exist_ok=True)
    (tmp_path / "src/part.scad").write_text(
        "cube_size_mm = 10;\nmcu_length_mm = 8;\nhub_od_mm = 12;\nwheel_bore_d_mm = 3.3;\n"
    )
    write_binary_stl(tmp_path / "stl/chassis.stl", chassis or cube_triangles(sx=20, sy=20, sz=8))
    write_binary_stl(tmp_path / "stl/wheel.stl", wheel or cube_triangles(sx=8, sy=8, sz=8))
    spec = base_spec()
    spec.update(assembly_block(wheel_xyz, **assembly_kw))
    (tmp_path / "docs/PRINT_SPEC.yaml").write_text(yaml.safe_dump(spec, sort_keys=False))
    return spec


def run_cli(project: Path):
    return subprocess.run(
        [sys.executable, str(VALIDATOR), str(project)],
        text=True, capture_output=True, check=False,
    )


def test_rpy_rx90_matches_urdf():
    matrix = rpy_matrix((90.0, 0.0, 0.0))
    tris = transform_tris([((0.0, 0.0, 1.0), (0.0, 0.0, 1.0), (0.0, 0.0, 1.0))], (0.0, 0.0, 0.0), (90.0, 0.0, 0.0))
    assert abs(tris[0][0][0]) < 1e-9
    assert abs(tris[0][0][1] + 1.0) < 1e-9
    assert abs(tris[0][0][2]) < 1e-9
    assert abs(matrix[1][2] + 1.0) < 1e-9


def test_l1_illegal_overlap_hard(tmp_path):
    spec = parse_spec(make_kit(tmp_path, (5, 5, 2)))
    placed = place_assembly(tmp_path, spec)
    hard = l1_occupancy(spec, placed)
    assert any("L1 collision" in item for item in hard)


def test_l1_clearance_pass_and_wheel_through_chassis_hard(tmp_path):
    spec = parse_spec(make_kit(tmp_path, (30, 0, 0), clearance=0.2))
    placed = place_assembly(tmp_path, spec)
    hard = l1_occupancy(spec, placed)
    assert hard == [], hard

    spec = parse_spec(make_kit(tmp_path, (6, 6, 0), clearance=0.2))
    placed = place_assembly(tmp_path, spec)
    hard = l1_occupancy(spec, placed)
    assert any("L1 collision" in item for item in hard)


def test_l2_sweep_pass_when_clear(tmp_path):
    spec = parse_spec(make_kit(tmp_path, (30, 0, 0), clearance=0.2))
    placed = place_assembly(tmp_path, spec)
    assert l1_occupancy(spec, placed) == []
    assert l2_sweep(spec, placed) == []


def test_l2_sweep_hard_on_self_collision(tmp_path):
    chassis = cube_triangles(sx=20, sy=8, sz=10)
    wheel = cube_triangles(sx=4, sy=8, sz=4)
    spec = parse_spec(
        make_kit(tmp_path, (5, 10, 5), chassis=chassis, wheel=wheel, clearance=0.2, axis=(0.0, 0.0, 1.0))
    )
    placed = place_assembly(tmp_path, spec)
    assert l1_occupancy(spec, placed) == [], l1_occupancy(spec, placed)
    hard = l2_sweep(spec, placed)
    assert any("L2 self-collision" in item for item in hard)


def test_l3_section_check_uses_declared_numbers():
    tau = hub_shear_mpa(0.049, 12.0, 3.3)
    assert tau is not None
    assert tau * 2.0 < ALLOWABLE_SHEAR_MPA["PETG"]
    fail = hub_shear_mpa(100.0, 12.0, 3.3)
    assert fail is not None
    assert fail * 2.0 > ALLOWABLE_SHEAR_MPA["PETG"]
    assert abs(moment_to_n_m(1000.0, "N_mm") - 1.0) < 1e-9


def test_l3_pass_fail_and_missing_required(tmp_path):
    spec = parse_spec(make_kit(tmp_path, (30, 0, 0)))
    assert l3_loads(spec) == []

    data = yaml.safe_load((tmp_path / "docs/PRINT_SPEC.yaml").read_text())
    data["loads"][1]["magnitude"] = 100.0
    spec = parse_spec(data)
    hard = l3_loads(spec)
    assert any("L3 hub shear" in item for item in hard)

    data = yaml.safe_load((tmp_path / "docs/PRINT_SPEC.yaml").read_text())
    data["loads"] = [load for load in data["loads"] if load["kind"] != "gravity"]
    spec = parse_spec(data)
    hard = l3_loads(spec)
    assert any("requires a gravity load" in item for item in hard)


def test_cli_overlap_hard(tmp_path):
    make_kit(tmp_path, (5, 5, 2))
    result = run_cli(tmp_path)
    assert result.returncode != 0
    assert "HARD:" in result.stdout
    assert "L1 collision" in result.stdout


def test_cli_missing_joint_limits_hard(tmp_path):
    make_kit(tmp_path, (30, 0, 0), limits=False)
    result = run_cli(tmp_path)
    assert result.returncode != 0
    assert "HARD:" in result.stdout
    assert "limits is required for revolute" in result.stdout


def test_cli_assumed_stall_hard(tmp_path):
    make_kit(tmp_path, (30, 0, 0), stall_source="assumed")
    result = run_cli(tmp_path)
    assert result.returncode != 0
    assert "HARD:" in result.stdout
    assert "cannot be assumed" in result.stdout


def test_cli_clearance_pass(tmp_path):
    make_kit(tmp_path, (30, 0, 0), clearance=0.2)
    result = run_cli(tmp_path)
    assert result.returncode == 0, result.stdout + result.stderr
    assert "RESULT: PASS" in result.stdout


def test_cli_skips_when_assembly_absent(tmp_path):
    spec = base_spec()
    spec["part"]["product_class"] = "bracket"
    spec.pop("hardware", None)
    spec["geometry"]["stl_files"] = [
        {"path": "stl/chassis.stl", "body": "chassis", "expected_shells": 1}
    ]
    (tmp_path / "docs").mkdir()
    (tmp_path / "src").mkdir()
    (tmp_path / "src/part.scad").write_text("cube_size_mm = 10;\n")
    (tmp_path / "docs/PRINT_SPEC.yaml").write_text(yaml.safe_dump(spec, sort_keys=False))
    result = run_cli(tmp_path)
    assert result.returncode == 0, result.stdout + result.stderr
    assert "no assembly block" in result.stdout
    assert "RESULT: PASS" in result.stdout
