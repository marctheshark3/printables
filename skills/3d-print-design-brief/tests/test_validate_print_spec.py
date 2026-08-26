from __future__ import annotations

import sys
from pathlib import Path

import yaml

SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS))

import print_spec as module  # noqa: E402

TEMPLATE = Path(__file__).resolve().parents[1] / "templates" / "PRINT_SPEC.yaml"


def valid_spec():
    return yaml.safe_load(TEMPLATE.read_text())


def test_template_passes_contract():
    assert module.validate(valid_spec()) == []


def test_rejects_non_parametric_backend():
    data = valid_spec()
    data["cad"]["parametric"] = False
    assert "cad.parametric must be true" in module.validate(data)


def test_rejects_overlapping_solids_policy():
    data = valid_spec()
    data["geometry"]["overlapping_solids_allowed"] = True
    assert "geometry.overlapping_solids_allowed must be false" in module.validate(data)


def test_rejects_ambiguous_or_missing_shell_contract():
    data = valid_spec()
    data["geometry"]["stl_files"][0].pop("expected_shells")
    errors = module.validate(data)
    assert "geometry.stl_files[0].expected_shells is required" in errors
    assert "geometry.stl_files[0].expected_shells must be an integer >= 1" in errors


def test_rejects_assumed_required_fit():
    data = valid_spec()
    data["fit"]["evidence"] = "assumed"
    assert any("required fit needs measured" in error for error in module.validate(data))


def test_rejects_dimension_without_tolerance():
    data = valid_spec()
    data["dimensions"][0].pop("tolerance_mm")
    assert "dimensions[0].tolerance_mm is required" in module.validate(data)


def test_rejects_features_smaller_than_two_nozzle_widths():
    data = valid_spec()
    data["geometry"]["min_wall_mm"] = 0.6
    data["geometry"]["min_feature_mm"] = 0.6
    errors = module.validate(data)
    assert "geometry.min_wall_mm must be at least 2x nozzle_mm" in errors
    assert "geometry.min_feature_mm must be at least 2x nozzle_mm" in errors


def test_rejects_wet_pla_without_drainage():
    data = valid_spec()
    data["service"]["environment"] = "wet"
    data["service"]["drainage"] = "none"
    data["manufacturing"]["material"] = "PLA"
    errors = module.validate(data)
    assert "wet service requires positive drainage" in errors
    assert "wet service cannot use PLA" in errors


def test_rejects_paths_outside_project():
    data = valid_spec()
    data["cad"]["source_files"] = ["../shared/part.scad"]
    data["geometry"]["stl_files"][0]["path"] = "/tmp/part.stl"
    errors = module.validate(data)
    assert any("cad.source_files" in error and "project-relative" in error for error in errors)
    assert any("geometry.stl_files[0].path" in error and "project-relative" in error for error in errors)


def test_check_files_is_fail_closed(tmp_path):
    data = valid_spec()
    errors = module.validate(data, project=tmp_path, check_files=True)
    assert any("declared file does not exist" in error for error in errors)


def test_wet_slots_drainage_passes():
    data = valid_spec()
    data["service"]["environment"] = "wet"
    data["service"]["drainage"] = "slots"
    data["manufacturing"]["material"] = "PETG"
    assert module.validate(data) == []


def test_wet_unknown_drainage_fails():
    data = valid_spec()
    data["service"]["environment"] = "wet"
    data["service"]["drainage"] = "mystery"
    data["manufacturing"]["material"] = "PETG"
    errors = module.validate(data)
    assert any("service.drainage must be one of" in error for error in errors)
    assert "wet service requires positive drainage" in errors


def test_datasheet_required_fit_passes_contract():
    data = valid_spec()
    data["fit"]["evidence"] = "datasheet"
    data["fit"]["coupon"] = "fit/example-bracket-fit-coupon.stl"
    assert module.validate(data) == []


def test_missing_coupon_file_fails(tmp_path):
    data = valid_spec()
    (tmp_path / "src").mkdir()
    (tmp_path / "stl").mkdir()
    (tmp_path / "src/example-bracket.scad").write_text("device_width_mm = 40;\n")
    (tmp_path / "stl/example-bracket.stl").write_bytes(b"solid")
    errors = module.validate(data, project=tmp_path, check_files=True)
    assert any("fit/example-bracket-fit-coupon.stl" in error for error in errors)


def test_parse_spec_roundtrip():
    parsed = module.parse_spec(valid_spec())
    assert parsed.backend == "openscad"
    assert parsed.stl_files[0].expected_shells == 1
    assert parsed.up_axis == "Z"
    assert parsed.extra_parameters == ()


def _interface(name, parameter, value_mm, source="datasheet"):
    return {
        "name": name,
        "parameter": parameter,
        "value_mm": value_mm,
        "tolerance_mm": 0.2,
        "source": source,
    }


def robot_spec():
    data = valid_spec()
    data["part"]["name"] = "robot-module-kit"
    data["part"]["product_class"] = "robot-module"
    data["part"]["purpose"] = "Numbered micro-robotics kit module."
    data["fit"] = {
        "required": True,
        "clearance_per_side_mm": 0.4,
        "evidence": "datasheet",
        "coupon": "fit/mcu-pocket-coupon.scad",
    }
    data["hardware"] = {
        "components": [
            {
                "id": "mcu",
                "mpn_or_generic": "ESP32-C3 Super Mini",
                "role": "mcu",
                "qty": 1,
                "envelope_mm": [22.5, 18.0, 4.5],
                "interfaces": [
                    _interface("mcu_length", "mcu_length_mm", 22.5),
                    _interface("mcu_width", "mcu_width_mm", 18.0),
                ],
            },
            {
                "id": "drive_left",
                "mpn_or_generic": "N20-class gear motor",
                "role": "motor",
                "qty": 1,
                "envelope_mm": [15.0, 12.0, 10.0],
                "interfaces": [
                    _interface("motor_gearbox_l", "motor_gearbox_l_mm", 15.0),
                ],
            },
        ]
    }
    data["wiring"] = {
        "voltage_domains": [
            {"name": "v3v3", "volts": 3.3},
            {"name": "v5", "volts": 5.0},
            {"name": "gnd", "volts": 0.0},
        ],
        "pin_map": [
            {"mcu_pin": "GPIO4", "function": "motor_left_in1", "voltage": 3.3, "net": "motor_left_in1"},
            {"mcu_pin": "GPIO8", "function": "led", "voltage": 3.3, "net": "led"},
            {"mcu_pin": "VIN", "function": "motor_vm", "voltage": 5.0, "net": "vm"},
        ],
        "nets": [
            {"name": "motor_left_in1", "voltage_domain": "v3v3"},
            {"name": "led", "voltage_domain": "v3v3"},
            {"name": "vm", "voltage_domain": "v5"},
        ],
        "connector_keepouts": [
            {
                "name": "usb_c",
                "parameter": "usb_c_keepout_w_mm",
                "width_mm": 13.5,
                "height_mm": 9.0,
                "source": "datasheet",
            }
        ],
        "cable_path_keepouts": [
            {
                "name": "motor_left",
                "parameter": "cable_path_motor_left_w_mm",
                "width_mm": 4.0,
                "height_mm": 2.0,
                "source": "measured",
            }
        ],
    }
    return data


def test_robot_module_with_hardware_and_wiring_passes():
    assert module.validate(robot_spec()) == []


def test_existing_class_without_hardware_still_passes():
    assert module.validate(valid_spec()) == []


def test_robot_module_empty_hardware_fails():
    data = robot_spec()
    data["hardware"]["components"] = []
    errors = module.validate(data)
    assert "robot-module requires non-empty hardware.components" in errors


def test_robot_module_missing_hardware_fails():
    data = robot_spec()
    data.pop("hardware")
    errors = module.validate(data)
    assert "robot-module requires non-empty hardware.components" in errors


def test_assumed_critical_mcu_fit_fails():
    data = robot_spec()
    data["hardware"]["components"][0]["interfaces"][0]["source"] = "assumed"
    errors = module.validate(data)
    assert any("cannot be assumed for critical role mcu" in error for error in errors)


def test_assumed_critical_servo_fit_fails():
    data = robot_spec()
    data["hardware"]["components"].append(
        {
            "id": "gripper_servo",
            "mpn_or_generic": "SG90",
            "role": "servo",
            "qty": 1,
            "envelope_mm": [22.8, 12.2, 22.8],
            "interfaces": [_interface("servo_body_x", "servo_body_x_mm", 22.8, source="assumed")],
        }
    )
    errors = module.validate(data)
    assert any("cannot be assumed for critical role servo" in error for error in errors)


def test_3v3_5v_collision_on_pin_fails():
    data = robot_spec()
    data["wiring"]["pin_map"].append(
        {"mcu_pin": "GPIO4", "function": "motor_vm_alias", "voltage": 5.0, "net": "vm"}
    )
    errors = module.validate(data)
    assert any("wiring 3V3/5V collision on pin GPIO4" in error for error in errors)


def test_3v3_5v_collision_on_net_fails():
    data = robot_spec()
    data["wiring"]["pin_map"].append(
        {"mcu_pin": "GPIO10", "function": "bad_net", "voltage": 3.3, "net": "vm"}
    )
    errors = module.validate(data)
    assert any("wiring 3V3/5V collision on net vm" in error for error in errors)


def test_robot_module_both_rails_without_collision_pass():
    data = robot_spec()
    assert module.validate(data) == []
    rails = {pin["voltage"] for pin in data["wiring"]["pin_map"]}
    assert 3.3 in rails and 5.0 in rails


def _pose(xyz, rpy=(0.0, 0.0, 0.0)):
    return {"xyz_mm": list(xyz), "rpy_deg": list(rpy)}


def assembled_robot_spec():
    data = robot_spec()
    data["geometry"]["stl_files"] = [
        {"path": "stl/chassis.stl", "body": "chassis", "expected_shells": 1},
        {"path": "stl/wheel.stl", "body": "wheel", "expected_shells": 1},
    ]
    data["cad"]["source_files"] = ["src/rover.scad"]
    data["assembly"] = {
        "frame": "assembled",
        "bodies": [
            {"id": "chassis", "body": "chassis", "parent": "world", "pose": _pose((0, 0, 0))},
            {"id": "wheel_left", "body": "wheel", "parent": "chassis", "pose": _pose((0, -20, 10), (90, 0, 0))},
            {"id": "wheel_right", "body": "wheel", "parent": "chassis", "pose": _pose((0, 20, 10), (-90, 0, 0))},
            {"id": "mcu", "hardware": "mcu", "parent": "chassis", "pose": _pose((8, 20, 4))},
            {"id": "drive_left", "hardware": "drive_left", "parent": "chassis", "pose": _pose((30, 4, 4))},
        ],
        "joints": [
            {
                "id": "wheel_left",
                "type": "revolute",
                "parent": "chassis",
                "child": "wheel_left",
                "axis": [0, 1, 0],
                "limits": {"min_deg": 0, "max_deg": 360},
                "clearance_per_side_mm": 0.15,
                "source": "datasheet",
            },
            {
                "id": "wheel_right",
                "type": "revolute",
                "parent": "chassis",
                "child": "wheel_right",
                "axis": [0, 1, 0],
                "limits": {"min_deg": 0, "max_deg": 360},
                "clearance_per_side_mm": 0.15,
                "source": "from-user",
            },
        ],
    }
    data["loads"] = [
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
            "source": "datasheet",
        },
        {
            "id": "stall_right",
            "kind": "moment",
            "target": "wheel_right",
            "magnitude": 0.049,
            "units": "N_m",
            "safety_factor": 2.0,
            "source": "datasheet",
        },
    ]
    data["sim"] = {
        "scene": {
            "id": "table-flat",
            "gravity_mm_s2": [0, 0, -9810],
            "floor": {"z_mm": 0},
            "friction": {"mu": 0.6, "source": "from-user"},
        }
    }
    return data


def test_robot_module_without_assembly_still_passes():
    assert module.validate(robot_spec()) == []


def test_assembled_robot_module_passes():
    assert module.validate(assembled_robot_spec()) == []


def test_assembly_unknown_body_fails():
    data = assembled_robot_spec()
    data["assembly"]["bodies"][1]["body"] = "not-a-body"
    errors = module.validate(data)
    assert any("not a geometry.stl_files body" in error for error in errors)


def test_assembly_unknown_hardware_fails():
    data = assembled_robot_spec()
    data["assembly"]["bodies"][3]["hardware"] = "not-a-part"
    errors = module.validate(data)
    assert any("not a hardware.components id" in error for error in errors)


def test_robot_module_assembly_missing_printed_body_fails():
    data = assembled_robot_spec()
    data["assembly"]["bodies"] = [
        item for item in data["assembly"]["bodies"] if item.get("body") != "wheel"
    ]
    errors = module.validate(data)
    assert any("missing printed body: wheel" in error for error in errors)


def test_revolute_joint_without_limits_fails():
    data = assembled_robot_spec()
    data["assembly"]["joints"][0].pop("limits")
    errors = module.validate(data)
    assert any("limits is required for revolute" in error for error in errors)


def test_assumed_stall_load_fails():
    data = assembled_robot_spec()
    data["loads"][1]["source"] = "assumed"
    errors = module.validate(data)
    assert any("loads[1].source cannot be assumed" in error for error in errors)


def test_robot_module_assembly_missing_gravity_fails():
    data = assembled_robot_spec()
    data["loads"] = [load for load in data["loads"] if load["kind"] != "gravity"]
    errors = module.validate(data)
    assert "robot-module assembly requires a gravity load" in errors


def test_markdown_is_not_read_as_contract(tmp_path):
    data = assembled_robot_spec()
    (tmp_path / "DESIGN.md").write_text(
        "assembly.bodies: [{id: ghost, body: invented}]\nloads: [{source: assumed}]\n",
        encoding="utf-8",
    )
    assert module.validate(data) == []
    parsed = module.parse_spec(data)
    assert all(body.id != "ghost" for body in parsed.assembly_bodies)
    assert all(load.source != "assumed" for load in parsed.loads)


def test_parse_spec_keeps_assembly_and_loads():
    parsed = module.parse_spec(assembled_robot_spec())
    assert parsed.assembly_frame == "assembled"
    assert {body.id for body in parsed.assembly_bodies} >= {"chassis", "wheel_left", "mcu"}
    assert {joint.id for joint in parsed.joints} == {"wheel_left", "wheel_right"}
    assert parsed.sim_scene is not None and parsed.sim_scene.id == "table-flat"
    assert any(load.kind == "moment" for load in parsed.loads)
