"""Optional AMS contracts must preserve the ordinary one-material path."""
from copy import deepcopy
from pathlib import Path
import sys

import pytest
import yaml

SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS))
import print_spec


def color_spec():
    data = yaml.safe_load((SCRIPTS.parent / "templates/PRINT_SPEC.yaml").read_text())
    data["manufacturing"]["material"] = "PLA"
    data["multi_material"] = {
        "mode": "color", "reason": "Readable assembly markings",
        "feeder": "ams-2-pro", "primary": "shell", "bed_temperature_c": 55,
        "materials": [
            {"id": name, "type": "PLA", "profile": "Generic PLA", "color": color,
             "nozzle_temperature_c": [190, 230], "bed_temperature_c": [35, 65]}
            for name, color in [("shell", "#202020"), ("mark", "#FFFFFF")]
        ],
        "regions": [
            {"id": name, "body": "bracket", "path": f"stl/{name}.stl",
             "material": name, "expected_shells": 1}
            for name in ("shell", "mark")
        ],
    }
    return data


def test_legacy_contract_has_no_material_plan():
    data = color_spec()
    del data["multi_material"]
    assert print_spec.validate(data) == []
    assert print_spec.parse_spec(data).multi_material is None


def test_color_regions_and_logical_ids_survive_parsing():
    data = color_spec()
    assert print_spec.validate(data) == []
    plan = print_spec.parse_spec(data).multi_material
    assert [m.id for m in plan.materials] == ["shell", "mark"]
    assert [(r.body, r.material, r.path) for r in plan.regions] == [
        ("bracket", "shell", "stl/shell.stl"),
        ("bracket", "mark", "stl/mark.stl"),
    ]


@pytest.mark.parametrize("mutation, message", [
    (lambda b: b["regions"][0].update(material="missing"), "unknown material"),
    (lambda b: b["regions"][0].update(body="missing"), "unknown body"),
    (lambda b: b["regions"][0].update(path="../outside.stl"), "project-relative"),
    (lambda b: b["materials"][1].update(type="TPU"), "unsupported AMS"),
    (lambda b: b["materials"][1].update(type="Generic PA-CF"), "unsupported AMS"),
    (lambda b: b["materials"][1].update(nozzle_temperature_c=[290, 320]), "300"),
    (lambda b: b.update(bed_temperature_c=80), "bed temperature"),
    (lambda b: b["materials"][1].update(id="shell"), "duplicate material"),
    (lambda b: b.update(regions=[]), "unused material"),
    (lambda b: b.update(mode="functional"), "bond_test"),
    (lambda b: b.update(materials=b["materials"] * 3), "four"),
])
def test_invalid_ams_contract_fails_closed(mutation, message):
    data = color_spec()
    mutation(data["multi_material"])
    assert any(message in error for error in print_spec.validate(data))


def test_support_interface_has_no_model_regions():
    data = color_spec()
    block = data["multi_material"]
    block.update(mode="support-interface", regions=[], interface_material="mark")
    block["materials"][1]["type"] = "Support for PLA/PETG"
    data["print"]["supports"] = "required"
    assert print_spec.validate(data) == []
    data["print"]["supports"] = "none"
    assert any("supports" in e for e in print_spec.validate(data))


def test_dedicated_support_filament_cannot_be_an_independent_model_body():
    data = color_spec()
    block = data["multi_material"]
    block.update(mode="support-interface", regions=[], interface_material="mark")
    block["materials"][1]["type"] = "Support for PLA/PETG"
    data["print"]["supports"] = "required"
    data["geometry"]["stl_files"].append({"path": "stl/other.stl", "body": "other", "expected_shells": 1, "material": "mark"})
    assert any("support material cannot be a model body" in e for e in print_spec.validate(data))


def test_functional_bond_evidence_must_exist_at_delivery(tmp_path):
    data = color_spec()
    block = data["multi_material"]
    block.update(mode="functional", bond_test={"source": "measured", "report": "fit/bond.md"})
    block["materials"][1]["type"] = "PETG"
    assert print_spec.validate(data) == []
    errors = print_spec.validate(data, project=tmp_path, check_files=True)
    assert any("fit/bond.md" in e for e in errors)


def test_additional_model_materials_obey_wet_service_policy():
    data = color_spec()
    data["service"].update(environment="wet", drainage="slots")
    data["manufacturing"]["material"] = "PETG"
    data["multi_material"]["mode"] = "functional"
    data["multi_material"]["materials"][0]["type"] = "PETG"
    data["multi_material"]["bond_test"] = {"source": "fit-tested", "report": "fit/bond.md"}
    assert any("wet service" in e for e in print_spec.validate(data))


def test_separate_body_can_select_a_logical_material():
    data = color_spec()
    data["multi_material"]["regions"] = []
    data["geometry"]["stl_files"].append({"path": "stl/other.stl", "body": "other", "expected_shells": 1, "material": "mark"})
    assert print_spec.validate(data) == []
    assert print_spec.parse_spec(data).stl_files[1].material == "mark"


def test_support_mode_cannot_bypass_functional_pair_evidence():
    data = color_spec()
    block = data["multi_material"]
    block.update(mode="support-interface", interface_material="support")
    block["materials"][1]["type"] = "PETG"
    block["materials"].append({**block["materials"][0], "id": "support", "type": "Support for PLA/PETG"})
    data["print"]["supports"] = "required"
    assert any("one polymer" in e for e in print_spec.validate(data))


@pytest.mark.parametrize("value", [None, [], "four colors", {"materials": [None, []]}])
def test_malformed_optional_block_returns_contract_errors(value):
    data = color_spec()
    data["multi_material"] = deepcopy(value)
    assert print_spec.validate(data)
