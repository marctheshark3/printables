"""Explicit local Studio profiles, native export, and post-export verification."""
from __future__ import annotations

import json
from pathlib import Path
import subprocess
import tempfile

from material_project import check_material_3mf, PLATES
from material_plan import SUPPORT_TYPES, studio_filament_type

def resolve_profile(path: Path, profile_root: Path | None = None) -> dict:
    """The CLI does not resolve the installed profiles' inheritance for us."""
    data = json.loads(path.read_text())
    root = profile_root
    if root is None:
        root = next((p for p in path.parents if (p / "machine").is_dir() and (p / "filament").is_dir()), path.parent)
    if not data.get("inherits"):
        return data
    index = {}
    for candidate in root.rglob("*.json"):
        value = json.loads(candidate.read_text())
        if isinstance(value, dict) and isinstance(value.get("name"), str):
            index[value["name"]] = value

    def resolve(value, seen):
        parent = value.get("inherits")
        if not parent:
            return value.copy()
        if parent in seen or parent not in index:
            raise ValueError(f"cannot resolve profile inheritance: {parent}")
        return {**resolve(index[parent], seen | {parent}), **value, "inherits": ""}

    return resolve(data, set())


def export_material_project(slicer: Path, project: Path, spec, out: Path, manifest: dict,
                            machine: Path, process: Path, filaments: dict[str, Path],
                            plate_type: str, *, profile_root: Path | None = None,
                            sliced: bool = False) -> Path:
    plan = spec.multi_material
    if set(filaments) != {m.id for m in plan.materials}:
        raise ValueError("provide exactly one --filament ID=profile.json for every logical material")
    if plate_type not in PLATES:
        raise ValueError("select a supported --plate-type: " + ", ".join(PLATES))
    machine_data = resolve_profile(machine, profile_root)
    if machine_data.get("printer_model") != "Bambu Lab P1S":
        raise ValueError("machine profile must target Bambu Lab P1S")
    nozzles = machine_data.get("nozzle_diameter", [])
    if not nozzles or any(float(n) != spec.nozzle_mm for n in nozzles):
        raise ValueError("machine profile nozzle differs from PRINT_SPEC")
    process_data = resolve_profile(process, profile_root)
    process_data.update(layer_height=str(spec.layer_height_mm), curr_bed_type=plate_type,
                        enable_prime_tower="1", flush_into_infill="0", flush_into_objects="0")
    destination = out / ("project.gcode.3mf" if sliced else "project.3mf")
    destination.unlink(missing_ok=True)
    with tempfile.TemporaryDirectory(prefix="material-profiles-") as temp:
        temp = Path(temp)
        (temp / "machine.json").write_text(json.dumps(machine_data))
        (temp / "process.json").write_text(json.dumps(process_data))
        loaded = []
        for i, material in enumerate(plan.materials, 1):
            value = resolve_profile(filaments[material.id], profile_root)
            if value.get("name") != material.profile:
                raise ValueError(f"profile name does not match material {material.id}: {material.profile}")
            support = any(str(flag) == "1" for flag in value.get("filament_is_support", []))
            if support != (material.type in SUPPORT_TYPES):
                raise ValueError(f"support/model profile role does not match material {material.id}")
            if value.get("filament_type") != [studio_filament_type(material.type)]:
                raise ValueError(f"filament polymer in profile does not match material {material.id}")
            temperatures = value.get("nozzle_temperature", [])
            temperatures = temperatures + value.get("nozzle_temperature_initial_layer", temperatures)
            if not temperatures or any(not material.nozzle_temperature_c[0] <= float(t) <= material.nozzle_temperature_c[1] for t in temperatures):
                raise ValueError(f"nozzle temperature in profile is outside material {material.id}'s range")
            value["filament_colour"] = [material.color]
            key = PLATES[plate_type]
            value[key] = [str(plan.bed_temperature_c)]
            value[key + "_initial_layer"] = [str(plan.bed_temperature_c)]
            path = temp / f"filament-{i}.json"
            path.write_text(json.dumps(value))
            loaded.append(str(path))
        argv = [str(slicer), "--load-settings", str(temp / "machine.json") + ";" + str(temp / "process.json"),
                "--load-filaments", ";".join(loaded), "--load-assemble-list", str((out / "assemble-list.json").resolve()),
                "--export-3mf", destination.name, "--outputdir", str(out.resolve())]
        if sliced:
            argv.extend(["--slice", "0"])
        result = subprocess.run(argv, text=True, capture_output=True, check=False)
        (out / "studio-export.log").write_text(result.stdout + result.stderr)
        try:
            if result.returncode:
                result_path = out / "result.json"
                detail = json.loads(result_path.read_text()).get("error_string", "") if result_path.is_file() else ""
                raise ValueError(f"Studio export failed ({result.returncode}): {detail}; see studio-export.log")
            check_material_3mf(destination, manifest, sliced=sliced)
        except (ValueError, OSError, KeyError):
            destination.unlink(missing_ok=True)
            raise
    return destination
