#!/usr/bin/env python3
"""Prepare a material-preserving Studio assemble list and inspect real 3MF output."""
from __future__ import annotations

import argparse
from dataclasses import asdict
import hashlib
import json
from pathlib import Path
import sys
from xml.etree import ElementTree as ET
import zipfile

SKILLS = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(SKILLS / "3d-print-design-brief/scripts"))
sys.path.insert(0, str(SKILLS / "3d-print-validate/scripts"))
from print_spec import load_spec
from material_plan import SUPPORT_TYPES, studio_filament_type
from stl_io import bbox_and_volume, load_binary_stl

CORE = "{http://schemas.microsoft.com/3dmanufacturing/core/2015/02}"
PRODUCTION = "{http://schemas.microsoft.com/3dmanufacturing/production/2015/06}"
PLATES = {
    "Textured PEI Plate": "textured_plate_temp", "High Temp Plate": "hot_plate_temp",
    "Cool Plate": "cool_plate_temp", "Engineering Plate": "eng_plate_temp",
}


def mesh_digest(tris, origin) -> str:
    faces = sorted(tuple(sorted(tuple(round((v[i] - origin[i]) * 1000) for i in range(3)) for v in tri)) for tri in tris)
    return hashlib.sha256(json.dumps(faces).encode()).hexdigest()


def _transform(tris, value):
    m = [float(n) for n in value.split()] if value else [1, 0, 0, 0, 1, 0, 0, 0, 1, 0, 0, 0]
    if len(m) != 12:
        raise ValueError("invalid 3MF transform")
    return [tuple(tuple(sum(v[k] * m[k * 3 + i] for k in range(3)) + m[9 + i] for i in range(3)) for v in tri) for tri in tris]


def _meshes(archive, model_path, identity, visited=frozenset()):
    key = (model_path, identity)
    if key in visited:
        raise ValueError("cyclic 3MF components")
    root = ET.fromstring(archive.read(model_path))
    obj = root.find(f"{CORE}resources/{CORE}object[@id='{identity}']")
    if obj is None:
        raise ValueError("missing 3MF mesh object")
    mesh = obj.find(CORE + "mesh")
    if mesh is not None:
        vertices = [tuple(float(v.get(c)) for c in ("x", "y", "z")) for v in mesh.findall(f"{CORE}vertices/{CORE}vertex")]
        triangles = [tuple(vertices[int(t.get(c))] for c in ("v1", "v2", "v3")) for t in mesh.findall(f"{CORE}triangles/{CORE}triangle")]
        if not triangles:
            raise ValueError("3MF contains an empty mesh")
        return [(identity, triangles)]
    result = []
    for component in obj.findall(f"{CORE}components/{CORE}component"):
        child_path = component.get(PRODUCTION + "path", model_path).lstrip("/")
        result.extend((leaf, _transform(tris, component.get("transform")))
                      for leaf, tris in _meshes(archive, child_path, component.get("objectid"), visited | {key}))
    return result


def write_material_project(project: Path, spec, out: Path) -> dict:
    plan = spec.multi_material
    if plan is None:
        raise ValueError("PRINT_SPEC has no multi_material plan")
    materials = [{**asdict(m), "filament": i} for i, m in enumerate(plan.materials, 1)]
    bodies, plates = [], []
    for index, body in enumerate(spec.stl_files, 1):
        low, high, _volume = bbox_and_volume(load_binary_stl(project / body.path)[1])
        shift = [(spec.build_volume_mm[i] - (high[i] - low[i])) / 2 - low[i] for i in (0, 1)] + [-low[2]]
        regions = plan.regions_for(body.body)
        support_settings = {
            "enable_support": "0" if spec.supports == "none" else "1",
            "support_on_build_plate_only": "1" if spec.supports == "build-plate-only" else "0",
            "support_filament": str(plan.filament_id(body.material or plan.primary)),
            "support_interface_filament": str(plan.filament_id(plan.interface_material or body.material or plan.primary)),
        }
        if plan.interface_material:
            support_settings.update({
                "support_top_z_distance": "0", "support_bottom_z_distance": "0",
                "support_interface_spacing": "0", "flush_into_infill": "0", "flush_into_objects": "0",
            })
        parts = [
            {"id": r.id, "path": r.path, "filament": plan.filament_id(r.material)} for r in regions
        ] if regions else [{"id": body.body, "path": body.path, "filament": plan.filament_id(body.material or plan.primary)}]
        for part in parts:
            part["mesh_digest"] = mesh_digest(load_binary_stl(project / part["path"])[1], low)
        objects = []
        for part in parts:
            item = {
                "path": str((project / part["path"]).resolve()), "count": 1,
                "filaments": [part["filament"]],
                "pos_x": [shift[0]], "pos_y": [shift[1]], "pos_z": [shift[2]],
                "print_params": support_settings,
            }
            if regions:
                item["assemble_index"] = [index]
            objects.append(item)
        plate = {"plate_name": body.body, "need_arrange": False, "objects": objects}
        if regions:
            plate["assembled_params"] = [{"assemble_index": index, "print_params": support_settings}]
        plates.append(plate)
        bodies.append({"body": body.body, "composite": body.path, "parts": parts, "translation_mm": shift,
                       "support_settings": support_settings})
    manifest = {
        "schema_version": 1, "printer": spec.printer, "mode": plan.mode,
        "nozzle_mm": spec.nozzle_mm, "layer_height_mm": spec.layer_height_mm,
        "supports": spec.supports,
        "reason": plan.reason, "materials": materials, "bodies": bodies,
        "bed_temperature_c": plan.bed_temperature_c,
        "interface_filament": plan.filament_id(plan.interface_material) if plan.interface_material else None,
        "ams_slots": None,
        "estimates": {"status": "not-sliced", "time_s": None, "filament_changes": None,
                      "flush_volume_mm3": None, "prime_tower_g": None,
                      "total_filament_g": None, "filament_g": None, "warnings": None},
    }
    out.mkdir(parents=True, exist_ok=True)
    for name in ("project.3mf", "project.gcode.3mf", "studio-export.log"):
        (out / name).unlink(missing_ok=True)
    (out / "material-plan.json").write_text(json.dumps(manifest, indent=2) + "\n")
    (out / "assemble-list.json").write_text(json.dumps({"plates": plates}, indent=2) + "\n")
    return manifest


def check_material_3mf(path: Path, manifest: dict, *, sliced: bool = False) -> dict:
    if not zipfile.is_zipfile(path):
        raise ValueError("export is not a 3MF zip")
    with zipfile.ZipFile(path) as archive:
        names = archive.namelist()
        has_gcode = any(name.lower().endswith(".gcode") for name in names)
        if has_gcode != sliced:
            raise ValueError("3MF sliced/unsliced state does not match the request")
        model = ET.fromstring(archive.read("3D/3dmodel.model"))
        if not any(e.tag.endswith("}item") for e in model.iter()):
            raise ValueError("3MF has no printable objects")
        config = ET.fromstring(archive.read("Metadata/model_settings.config"))
        settings = json.loads(archive.read("Metadata/project_settings.config"))
        objects = config.findall("object")
        if len(objects) != len(manifest["bodies"]):
            raise ValueError("3MF printed body count differs from material plan")
        actual = []
        for body in manifest["bodies"]:
            plate = next((p for p in config.findall("plate") if p.find("metadata[@key='plater_name']") is not None
                          and p.find("metadata[@key='plater_name']").get("value") == body["body"]), None)
            if plate is None or len(plate.findall("model_instance")) != 1:
                raise ValueError("3MF body/plate grouping differs from material plan")
            identity = plate.find("model_instance/metadata[@key='object_id']").get("value")
            obj = next(o for o in objects if o.get("id") == identity)
            meshes = _meshes(archive, "3D/3dmodel.model", identity)
            instance = model.find(f"{CORE}build/{CORE}item[@objectid='{identity}']")
            if instance is None or not meshes:
                raise ValueError("3MF has no printable body instance")
            meshes = [(leaf, _transform(tris, instance.get("transform"))) for leaf, tris in meshes]
            low = bbox_and_volume([tri for _leaf, tris in meshes for tri in tris])[0]
            observed = []
            for leaf, tris in meshes:
                part = obj.find(f"part[@id='{leaf}']")
                metadata = part if part is not None else obj
                extruder = metadata.find("metadata[@key='extruder']")
                if extruder is None:
                    extruder = obj.find("metadata[@key='extruder']")
                slot = int(extruder.get("value")) if extruder is not None else 1
                observed.append((slot, mesh_digest(tris, low)))
            expected = [(p["filament"], p["mesh_digest"]) for p in body["parts"]]
            if sorted(observed) != sorted(expected):
                raise ValueError("3MF material assignments or region geometry differ from material plan")
            actual.append([slot for slot, _digest in observed])
            for key, expected_value in body["support_settings"].items():
                metadata = obj.find(f"metadata[@key='{key}']")
                value = metadata.get("value") if metadata is not None else settings.get(key)
                if value != expected_value:
                    raise ValueError(f"3MF support settings differ from material plan: {key}")
        if settings.get("printer_model") != "Bambu Lab P1S" or settings.get("nozzle_diameter") != [str(manifest["nozzle_mm"])]:
            raise ValueError("3MF printer/nozzle differs from material plan")
        if float(settings.get("layer_height", -1)) != manifest["layer_height_mm"]:
            raise ValueError("3MF layer height differs from material plan")
        bed_key = PLATES.get(settings.get("curr_bed_type"))
        temperatures = settings.get(bed_key, []) if bed_key else []
        if not temperatures or any(float(t) != manifest["bed_temperature_c"] for t in temperatures):
            raise ValueError("3MF bed temperature differs from material plan")
        colors = settings.get("filament_colour", [])
        if [c.upper()[:7] for c in colors] != [m["color"].upper() for m in manifest["materials"]]:
            raise ValueError("3MF filament colors differ from material plan")
        materials = manifest["materials"]
        if settings.get("filament_type") != [studio_filament_type(m["type"]) for m in materials]:
            raise ValueError("3MF filament polymers differ from material plan")
        if settings.get("filament_settings_id") != [m["profile"] for m in materials]:
            raise ValueError("3MF filament preset identities differ from material plan")
        if settings.get("filament_is_support") != ["1" if m["type"] in SUPPORT_TYPES else "0" for m in materials]:
            raise ValueError("3MF support/model filament roles differ from material plan")
        for key in ("nozzle_temperature", "nozzle_temperature_initial_layer"):
            values = settings.get(key, [])
            if len(values) != len(materials) or any(
                not m["nozzle_temperature_c"][0] <= float(t) <= m["nozzle_temperature_c"][1]
                for m, t in zip(materials, values)
            ):
                raise ValueError(f"3MF nozzle temperature differs from material plan: {key}")
        if len(config.findall("plate")) != len(manifest["bodies"]):
            raise ValueError("3MF plate count differs from material plan")
    return {"path": str(path), "sliced": sliced, "bodies": len(objects), "assignments": actual}


def slice_estimates(path: Path) -> dict:
    """Only values present in real Studio slice metadata; no inferred purge cost."""
    with zipfile.ZipFile(path) as archive:
        config = ET.fromstring(archive.read("Metadata/slice_info.config"))
    plates = config.findall("plate")
    times, weights, filament_g, warnings = [], [], {}, []
    for plate in plates:
        values = {m.get("key"): m.get("value") for m in plate.findall("metadata")}
        if "prediction" in values:
            times.append(float(values["prediction"]))
        if "weight" in values:
            weights.append(float(values["weight"]))
        for filament in plate.findall("filament"):
            if filament.get("used_g") is not None:
                identity = filament.get("id")
                filament_g[identity] = filament_g.get(identity, 0) + float(filament.get("used_g"))
        warnings.extend(dict(w.attrib) for w in plate.findall("warning"))
    return {"status": "sliced", "time_s": sum(times) if len(times) == len(plates) and plates else None,
            "total_filament_g": sum(weights) if len(weights) == len(plates) and plates else None,
            "filament_g": filament_g or None, "filament_changes": None,
            "flush_volume_mm3": None, "prime_tower_g": None, "warnings": warnings}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    prepare = commands.add_parser("plan")
    prepare.add_argument("project", type=Path)
    prepare.add_argument("--out", type=Path)
    check = commands.add_parser("check-3mf")
    check.add_argument("path", type=Path)
    check.add_argument("--plan", required=True, type=Path)
    check.add_argument("--sliced", action="store_true")
    args = parser.parse_args()
    try:
        if args.command == "check-3mf":
            print(json.dumps(check_material_3mf(args.path, json.loads(args.plan.read_text()), sliced=args.sliced)))
        else:
            project = args.project.resolve()
            spec, errors = load_spec(project / "docs/PRINT_SPEC.yaml", project=project, check_files=True)
            if errors:
                raise ValueError("; ".join(errors))
            write_material_project(project, spec, args.out or project / "slice")
            print("MATERIAL_PLAN: " + str(args.out or project / "slice"))
        return 0
    except (ValueError, KeyError, OSError, ET.ParseError, zipfile.BadZipFile) as error:
        print(f"HARD: {error}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
