from __future__ import annotations

import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[3]
BRIEF = ROOT / "skills" / "3d-print-design-brief" / "scripts"
SIM = ROOT / "skills" / "3d-print-sim" / "scripts"
sys.path.insert(0, str(BRIEF))
sys.path.insert(0, str(SIM))

from emit_mjcf import SCHEMA, emit_mjcf  # noqa: E402
from print_spec import parse_spec, validate  # noqa: E402


def tiny_spec():
    return {
        "schema_version": 1,
        "part": {"name": "tiny-kit", "revision": "0.1.0", "product_class": "robot-module", "purpose": "mjcf"},
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
            {"name": "cube", "parameter": "cube_size_mm", "value_mm": 10, "tolerance_mm": 0.1, "source": "measured"},
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
                    "envelope_mm": [8.0, 6.0, 4.0],
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
        "assembly": {
            "frame": "assembled",
            "bodies": [
                {
                    "id": "chassis", "body": "chassis", "parent": "world",
                    "pose": {"xyz_mm": [0.0, 0.0, 0.0], "rpy_deg": [0.0, 0.0, 0.0]},
                },
                {
                    "id": "wheel_left", "body": "wheel", "parent": "chassis",
                    "pose": {"xyz_mm": [10.0, -5.0, 4.0], "rpy_deg": [90.0, 0.0, 0.0]},
                },
                {
                    "id": "mcu", "hardware": "mcu", "parent": "chassis",
                    "pose": {"xyz_mm": [1.0, 1.0, 2.0], "rpy_deg": [0.0, 0.0, 0.0]},
                },
            ],
            "joints": [
                {
                    "id": "wheel_left",
                    "type": "revolute",
                    "parent": "chassis",
                    "child": "wheel_left",
                    "axis": [0.0, 1.0, 0.0],
                    "limits": {"min_deg": 0, "max_deg": 360},
                    "clearance_per_side_mm": 0.15,
                    "source": "datasheet",
                }
            ],
        },
        "loads": [
            {
                "id": "gravity", "kind": "gravity", "target": "assembled",
                "magnitude": 9810, "units": "mm_s2", "safety_factor": 2.0, "source": "from-user",
            },
            {
                "id": "stall_left", "kind": "moment", "target": "wheel_left",
                "magnitude": 0.049, "units": "N_m", "safety_factor": 2.0, "source": "datasheet",
                "section": {"outer_parameter": "hub_od_mm", "inner_parameter": "wheel_bore_d_mm"},
            },
        ],
        "sim": {
            "scene": {
                "id": "table-flat",
                "gravity_mm_s2": [0.0, 0.0, -9810.0],
                "floor": {"z_mm": 0.0},
                "friction": {"mu": 0.6, "source": "from-user"},
            }
        },
    }


GOLDEN_MJCF = """<mujoco model="tiny-kit">
  <!-- schema printables-mjcf-v1 ; emitted from PRINT_SPEC; not a contract -->
  <compiler angle="degree" coordinate="local" meshdir="stl"/>
  <option gravity="0.000 0.000 -9810.000"/>
  <asset>
    <mesh name="chassis" file="chassis.stl"/>
    <mesh name="wheel" file="wheel.stl"/>
  </asset>
  <worldbody>
    <geom name="floor" type="plane" size="200.000 200.000 0.100" pos="0.000 0.000 0.000"/>
    <body name="chassis" pos="0.000 0.000 0.000" euler="0.000 0.000 0.000">
      <geom type="mesh" mesh="chassis"/>
    </body>
    <body name="wheel_left" pos="10.000 -5.000 4.000" euler="90.000 0.000 0.000">
      <joint name="wheel_left" type="hinge" axis="0.000 1.000 0.000" range="0.000 360.000"/>
      <geom type="mesh" mesh="wheel"/>
    </body>
    <body name="mcu" pos="1.000 1.000 2.000" euler="0.000 0.000 0.000">
      <geom type="box" size="4.000 3.000 2.000" pos="4.000 3.000 2.000"/>
    </body>
  </worldbody>
</mujoco>
"""


def test_emit_mjcf_golden_without_mujoco():
    assert "mujoco" not in sys.modules
    data = tiny_spec()
    assert validate(data) == [], validate(data)
    spec = parse_spec(data)
    xml = emit_mjcf(spec)
    assert SCHEMA in xml
    assert xml == GOLDEN_MJCF
    assert "import mujoco" not in Path(SIM / "emit_mjcf.py").read_text(encoding="utf-8")
    dumped = yaml.safe_dump(data)
    assert "mujoco" not in dumped
    assert "mujoco" not in sys.modules
