"""Exercise the public CLI and exported material geometry, without a live printer."""
import json
from dataclasses import replace
from pathlib import Path
import shutil
import sys
import subprocess
from xml.etree import ElementTree as ET
from zipfile import ZipFile

import pytest
import yaml
from test_slice_project import run_slice

REPO = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(REPO / "skills/3d-print-multi-material/scripts"))
from material_project import CORE, check_material_3mf, slice_estimates
from studio_export import export_material_project
from print_spec import load_spec
from stl_io import load_binary_stl


def project_copy(tmp_path, name="two-color-enclosure-lid"):
    target = tmp_path / name
    shutil.copytree(REPO / "examples" / name, target)
    return target


def test_plan_retains_region_frame_and_logical_materials(tmp_path):
    project = project_copy(tmp_path)
    result = run_slice(project)
    assert result.returncode == 0, result.stdout + result.stderr
    plan = json.loads((project / "slice/material-plan.json").read_text())
    listing = json.loads((project / "slice/assemble-list.json").read_text())
    parts = listing["plates"][0]["objects"]
    assert [p["filaments"] for p in parts] == [[1], [2]]
    assert [p["assemble_index"] for p in parts] == [[1], [1]]
    assert parts[0]["pos_z"] == parts[1]["pos_z"] == [0]
    assert plan["ams_slots"] is None
    assert all(value is None for key, value in plan["estimates"].items() if key != "status")
    assert not list((project / "slice").glob("*.3mf"))


def test_support_material_is_only_the_interface(tmp_path):
    project = project_copy(tmp_path, "support-interface-coupon")
    assert run_slice(project).returncode == 0
    listing = json.loads((project / "slice/assemble-list.json").read_text())
    settings = listing["plates"][0]["objects"][0]["print_params"]
    assert settings["support_filament"] == "1"
    assert settings["support_interface_filament"] == "2"
    assert settings["flush_into_infill"] == "0"
    assert settings["enable_support"] == "1"


def test_regenerating_plan_invalidates_old_exports(tmp_path):
    project = project_copy(tmp_path)
    assert run_slice(project).returncode == 0
    old = project / "slice/project.3mf"
    old.write_bytes(b"older material assignments")
    assert run_slice(project).returncode == 0
    assert not old.exists()


def native_fixture(path, project, plan, *, drop_mark=False, wrong_filament=False, settings_override=None, support_override=None):
    """Small standard 3MF with native grouping and explicit part assignments."""
    model = ET.Element(CORE + "model")
    resources = ET.SubElement(model, CORE + "resources")
    group = ET.SubElement(resources, CORE + "object", id="99")
    components = ET.SubElement(group, CORE + "components")
    config = ET.Element("config")
    obj = ET.SubElement(config, "object", id="99")
    for key, value in {**plan["bodies"][0]["support_settings"], **(support_override or {})}.items():
        ET.SubElement(obj, "metadata", key=key, value=value)
    for i, part in enumerate(plan["bodies"][0]["parts"], 1):
        component = ET.SubElement(components, CORE + "component", objectid=str(i))
        if drop_mark and i == 2:
            component.set("transform", "1 0 0 0 1 0 0 0 1 0 0 -2.8")
        entry = ET.SubElement(resources, CORE + "object", id=str(i))
        mesh = ET.SubElement(entry, CORE + "mesh")
        vertices = ET.SubElement(mesh, CORE + "vertices")
        triangles = ET.SubElement(mesh, CORE + "triangles")
        for index, tri in enumerate(load_binary_stl(project / part["path"])[1]):
            for vertex in tri:
                ET.SubElement(vertices, CORE + "vertex", **dict(zip(("x", "y", "z"), map(str, vertex))))
            ET.SubElement(triangles, CORE + "triangle", v1=str(index * 3), v2=str(index * 3 + 1), v3=str(index * 3 + 2))
        metadata = ET.SubElement(obj, "part", id=str(i))
        ET.SubElement(metadata, "metadata", key="extruder", value="1" if wrong_filament else str(part["filament"]))
    ET.SubElement(ET.SubElement(model, CORE + "build"), CORE + "item", objectid="99")
    plate = ET.SubElement(config, "plate")
    ET.SubElement(plate, "metadata", key="plater_name", value=plan["bodies"][0]["body"])
    ET.SubElement(ET.SubElement(plate, "model_instance"), "metadata", key="object_id", value="99")
    with ZipFile(path, "w") as archive:
        archive.writestr("3D/3dmodel.model", ET.tostring(model))
        archive.writestr("Metadata/model_settings.config", ET.tostring(config))
        archive.writestr("Metadata/project_settings.config", json.dumps({
            "filament_colour": [m["color"] for m in plan["materials"]],
            "printer_model": "Bambu Lab P1S", "nozzle_diameter": [str(plan["nozzle_mm"])],
            "layer_height": str(plan["layer_height_mm"]), "curr_bed_type": "Textured PEI Plate",
            "textured_plate_temp": [str(plan["bed_temperature_c"])] * len(plan["materials"]),
            "textured_plate_temp_initial_layer": [str(plan["bed_temperature_c"])] * len(plan["materials"]),
            "filament_type": ["PLA"] * len(plan["materials"]),
            "filament_settings_id": [m["profile"] for m in plan["materials"]],
            "filament_is_support": ["0"] * len(plan["materials"]),
            "nozzle_temperature": ["220"] * len(plan["materials"]),
            "nozzle_temperature_initial_layer": ["220"] * len(plan["materials"]),
            **(settings_override or {}),
        }))


@pytest.mark.parametrize("corruption", [None, "drop_mark", "wrong_filament", "empty"])
def test_export_checker_checks_actual_geometry_and_assignments(tmp_path, corruption):
    project = project_copy(tmp_path)
    assert run_slice(project).returncode == 0
    plan = json.loads((project / "slice/material-plan.json").read_text())
    output = tmp_path / "project.3mf"
    if corruption == "empty":
        with ZipFile(output, "w") as archive:
            archive.writestr("3D/3dmodel.model", f'<model xmlns="{CORE[1:-1]}"><resources/><build/></model>')
    else:
        native_fixture(output, project, plan, **({corruption: True} if corruption else {}))
    if corruption:
        with pytest.raises(ValueError):
            check_material_3mf(output, plan)
    else:
        assert check_material_3mf(output, plan)["assignments"] == [[1, 2]]


def test_pack_includes_regions_and_rejects_stale_material_plan(tmp_path):
    project = project_copy(tmp_path)
    assert run_slice(project).returncode == 0
    command = [sys.executable, str(REPO / "skills/3d-print-pack/scripts/pack_project.py"), str(project)]
    result = subprocess.run(command, capture_output=True, text=True)
    assert result.returncode == 0, result.stdout + result.stderr
    with ZipFile(project / "pack/two-color-enclosure-lid.zip") as archive:
        assert {"stl/shell.stl", "stl/mark.stl", "slice/material-plan.json", "MANIFEST.sha256"} <= set(archive.namelist())
        assert "slice/assemble-list.json" not in archive.namelist()
    spec_path = project / "docs/PRINT_SPEC.yaml"
    spec = yaml.safe_load(spec_path.read_text())
    spec["multi_material"]["materials"][1]["color"] = "#DD4400"
    spec_path.write_text(yaml.safe_dump(spec))
    result = subprocess.run(command, capture_output=True, text=True)
    assert result.returncode == 1
    assert "differs from current PRINT_SPEC" in result.stdout + result.stderr


def test_estimates_use_slice_metadata_and_leave_unreported_waste_unknown(tmp_path):
    path = tmp_path / "sliced.3mf"
    with ZipFile(path, "w") as archive:
        archive.writestr("Metadata/slice_info.config", '<config><plate><metadata key="prediction" value="900"/><metadata key="weight" value="4.2"/><filament id="2" used_g="0.5"/><warning msg="temperature" level="3"/></plate></config>')
    result = slice_estimates(path)
    assert result["time_s"] == 900
    assert result["total_filament_g"] == 4.2
    assert result["filament_g"] == {"2": 0.5}
    assert result["flush_volume_mm3"] is None
    assert result["prime_tower_g"] is None
    assert result["warnings"][0]["msg"] == "temperature"


@pytest.mark.parametrize("bad, message", [("printer", "P1S"), ("nozzle", "nozzle"), ("polymer", "polymer")])
def test_profiles_must_match_the_declared_printer_and_materials(tmp_path, bad, message):
    project = project_copy(tmp_path)
    assert run_slice(project).returncode == 0
    spec, _errors = load_spec(project / "docs/PRINT_SPEC.yaml")
    manifest = json.loads((project / "slice/material-plan.json").read_text())
    machine = {"printer_model": "H2D" if bad == "printer" else "Bambu Lab P1S", "nozzle_diameter": ["0.6" if bad == "nozzle" else "0.4"]}
    filament = {"name": spec.multi_material.materials[0].profile, "filament_type": ["PETG" if bad == "polymer" else "PLA"], "nozzle_temperature": ["220"]}
    for name, data in [("machine", machine), ("process", {}), ("filament", filament)]:
        (tmp_path / (name + ".json")).write_text(json.dumps(data))
    with pytest.raises(ValueError, match=message):
        export_material_project(tmp_path / "unused-slicer", project, spec, project / "slice", manifest,
                                tmp_path / "machine.json", tmp_path / "process.json",
                                {m.id: tmp_path / "filament.json" for m in spec.multi_material.materials}, "Textured PEI Plate")


@pytest.mark.parametrize("policy", ["none", "required", "build-plate-only"])
def test_color_regions_keep_the_support_policy_on_the_assembled_body(tmp_path, policy):
    project = project_copy(tmp_path)
    path = project / "docs/PRINT_SPEC.yaml"
    data = yaml.safe_load(path.read_text())
    data["print"]["supports"] = policy
    path.write_text(yaml.safe_dump(data))
    assert run_slice(project).returncode == 0
    plate = json.loads((project / "slice/assemble-list.json").read_text())["plates"][0]
    settings = plate["assembled_params"][0]["print_params"]
    assert settings["enable_support"] == ("0" if policy == "none" else "1")
    assert settings["support_on_build_plate_only"] == ("1" if policy == "build-plate-only" else "0")


@pytest.mark.parametrize("settings, message", [
    ({"filament_type": ["PLA", "PETG"]}, "polymer"),
    ({"filament_settings_id": ["wrong preset", "wrong preset"]}, "preset"),
    ({"nozzle_temperature": ["220", "300"]}, "nozzle temperature"),
    ({"nozzle_temperature_initial_layer": ["300", "220"]}, "nozzle temperature"),
    ({"textured_plate_temp_initial_layer": ["100", "100"]}, "bed temperature"),
])
def test_native_export_and_pack_reject_changed_filament_settings(tmp_path, settings, message):
    project = project_copy(tmp_path)
    assert run_slice(project).returncode == 0
    plan = json.loads((project / "slice/material-plan.json").read_text())
    output = project / "slice/project.3mf"
    native_fixture(output, project, plan, settings_override=settings)
    with pytest.raises(ValueError, match=message):
        check_material_3mf(output, plan)
    result = subprocess.run([sys.executable, str(REPO / "skills/3d-print-pack/scripts/pack_project.py"), str(project)], capture_output=True, text=True)
    assert result.returncode == 1
    assert message in result.stdout + result.stderr


def test_native_export_rejects_a_disabled_required_support_policy(tmp_path):
    project = project_copy(tmp_path)
    path = project / "docs/PRINT_SPEC.yaml"
    data = yaml.safe_load(path.read_text())
    data["print"]["supports"] = "required"
    path.write_text(yaml.safe_dump(data))
    assert run_slice(project).returncode == 0
    plan = json.loads((project / "slice/material-plan.json").read_text())
    output = project / "slice/project.3mf"
    native_fixture(output, project, plan, support_override={"enable_support": "0"})
    with pytest.raises(ValueError, match="support settings"):
        check_material_3mf(output, plan)


@pytest.mark.parametrize("kind, native_type, accepted", [("TPU for AMS", "TPU-AMS", True), ("Bambu PAHT-CF", "PA-CF", True), ("TPU for AMS", "TPU", False)])
def test_supported_studio_filament_alias_reaches_native_export(tmp_path, monkeypatch, kind, native_type, accepted):
    project = project_copy(tmp_path)
    assert run_slice(project).returncode == 0
    spec, _errors = load_spec(project / "docs/PRINT_SPEC.yaml")
    material = replace(spec.multi_material.materials[0], type=kind, profile="Bambu " + kind.removeprefix("Bambu ") + " @BBL P1P")
    spec = replace(spec, multi_material=replace(spec.multi_material, materials=(material, *spec.multi_material.materials[1:])))
    manifest = json.loads((project / "slice/material-plan.json").read_text())
    profiles = {
        "machine": {"printer_model": "Bambu Lab P1S", "nozzle_diameter": ["0.4"]},
        "process": {},
        "shell": {"name": material.profile, "filament_type": [native_type], "nozzle_temperature": ["220"]},
        "mark": {"name": spec.multi_material.materials[1].profile, "filament_type": ["PLA"], "nozzle_temperature": ["220"]},
    }
    for name, data in profiles.items():
        (tmp_path / (name + ".json")).write_text(json.dumps(data))
    class ExportReached(Exception):
        pass
    def native_export(*_args, **_kwargs):
        raise ExportReached
    monkeypatch.setattr("studio_export.subprocess.run", native_export)
    with pytest.raises(ExportReached if accepted else ValueError, match=None if accepted else "polymer"):
        export_material_project(tmp_path / "slicer", project, spec, project / "slice", manifest,
                                tmp_path / "machine.json", tmp_path / "process.json",
                                {identity: tmp_path / (identity + ".json") for identity in ["shell", "mark"]}, "Textured PEI Plate")
