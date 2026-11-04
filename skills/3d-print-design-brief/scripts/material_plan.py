"""Optional, logical material assignments; physical AMS slots belong to job setup."""
from __future__ import annotations

from dataclasses import dataclass
import math
from pathlib import Path
import re


AMS_TYPES = {
    "PLA", "PETG", "ABS", "ASA", "PET", "PA", "PC", "PVA", "BVOH",
    "PP", "POM", "HIPS", "Bambu PLA-CF", "Bambu PAHT-CF", "Bambu PETG-CF",
    "Support for PLA/PETG", "TPU for AMS",
}
SUPPORT_TYPES = {"Support for PLA/PETG", "PVA", "BVOH"}
ABRASIVE_TYPES = {"Bambu PLA-CF", "Bambu PAHT-CF", "Bambu PETG-CF"}
STUDIO_FILAMENT_TYPES = {
    "Bambu PLA-CF": "PLA-CF", "Bambu PAHT-CF": "PA-CF", "Bambu PETG-CF": "PETG-CF",
    "Support for PLA/PETG": "PLA", "TPU for AMS": "TPU-AMS",
}


def studio_filament_type(material_type: str) -> str:
    return STUDIO_FILAMENT_TYPES.get(material_type, material_type)


@dataclass(frozen=True)
class Material:
    id: str
    type: str
    profile: str
    color: str
    nozzle_temperature_c: tuple[float, float]
    bed_temperature_c: tuple[float, float]


@dataclass(frozen=True)
class MaterialRegion:
    id: str
    body: str
    path: str
    material: str
    expected_shells: int
    min_wall_mm: float


@dataclass(frozen=True)
class MaterialPlan:
    mode: str
    reason: str
    primary: str
    bed_temperature_c: float
    materials: tuple[Material, ...]
    regions: tuple[MaterialRegion, ...]
    interface_material: str | None
    bond_report: str | None

    def regions_for(self, body: str) -> tuple[MaterialRegion, ...]:
        return tuple(region for region in self.regions if region.body == body)

    def filament_id(self, material: str) -> int:
        return next(i for i, item in enumerate(self.materials, 1) if item.id == material)


def _number(value) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value)


def _text(value) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _relative(value) -> bool:
    return _text(value) and not Path(value).is_absolute() and ".." not in Path(value).parts


def _range(value, maximum: float) -> bool:
    return (isinstance(value, list) and len(value) == 2
            and all(_number(v) for v in value) and 0 <= value[0] <= value[1] <= maximum)


def validate_material_plan(data: dict, *, project: Path | None = None,
                           check_files: bool = False) -> list[str]:
    if "multi_material" not in data:
        return []
    block = data["multi_material"]
    if not isinstance(block, dict):
        return ["multi_material must be a mapping when present"]
    errors = []
    mode = block.get("mode")
    if mode not in ("color", "support-interface", "functional"):
        errors.append("multi_material.mode must be color, support-interface, or functional")
    if not _text(block.get("reason")):
        errors.append("multi_material.reason must explain the benefit")
    if block.get("feeder") != "ams-2-pro" or data["manufacturing"]["printer"] != "bambu-lab-p1s":
        errors.append("multi_material currently supports bambu-lab-p1s with feeder ams-2-pro")
    materials = block.get("materials")
    if not isinstance(materials, list) or not 2 <= len(materials) <= 4:
        return errors + ["multi_material.materials requires two to four logical filaments"]
    by_id = {}
    bed = block.get("bed_temperature_c")
    if not _number(bed) or not 0 <= bed <= 100:
        errors.append("multi_material shared bed temperature must be within 0–100 C")
    for i, material in enumerate(materials):
        label = f"multi_material.materials[{i}]"
        if not isinstance(material, dict) or not _text(material.get("id")):
            errors.append(f"{label} requires a non-empty material id")
            continue
        identity = material["id"]
        if identity in by_id:
            errors.append(f"duplicate material id: {identity}")
        by_id[identity] = material
        kind = material.get("type")
        if not isinstance(kind, str) or kind not in AMS_TYPES:
            errors.append(f"{label}: unsupported AMS filament type {kind!r}")
        if not _text(material.get("profile")):
            errors.append(f"{label}.profile must name the installed slicer preset")
        if not isinstance(material.get("color"), str) or not re.fullmatch(r"#[0-9A-Fa-f]{6}", material["color"]):
            errors.append(f"{label}.color must be #RRGGBB")
        if not _range(material.get("nozzle_temperature_c"), 300):
            errors.append(f"{label}.nozzle_temperature_c must be [min, max] within 0–300 C")
        interval = material.get("bed_temperature_c")
        if not _range(interval, 100):
            errors.append(f"{label}.bed_temperature_c must be [min, max] within 0–100 C")
        elif _number(bed) and not interval[0] <= bed <= interval[1]:
            errors.append(f"{label}: shared bed temperature is outside the filament's range")
        if isinstance(kind, str) and kind in ABRASIVE_TYPES:
            manufacturing = data["manufacturing"]
            if any(manufacturing.get(key) != "hardened-steel" for key in ("nozzle_material", "extruder_gears")):
                errors.append(f"{label}: abrasive filament requires hardened-steel nozzle and extruder_gears")
            if manufacturing["nozzle_mm"] < 0.4:
                errors.append(f"{label}: abrasive filament needs at least a 0.4 mm nozzle")
        if kind in ("PVA", "BVOH") and material.get("dry") is not True:
            errors.append(f"{label}: PVA/BVOH must be confirmed dry")
    if errors:
        return errors
    primary = block.get("primary")
    if not isinstance(primary, str) or primary not in by_id:
        errors.append("multi_material.primary references an unknown material")
    elif by_id[primary].get("type") != data["manufacturing"]["material"]:
        errors.append("manufacturing.material must equal the primary material type")

    bodies = {b["body"]: b for b in data["geometry"]["stl_files"]
              if isinstance(b, dict) and _text(b.get("body"))}
    if len(bodies) != len(data["geometry"]["stl_files"]):
        errors.append("multi-material printed bodies need unique non-empty body names")
    used = set()
    paths = []
    regions = block.get("regions", [])
    if not isinstance(regions, list):
        errors.append("multi_material.regions must be a list")
        regions = []
    seen = set()
    region_paths = {b.get("path") for b in bodies.values() if isinstance(b.get("path"), str)}
    for i, region in enumerate(regions):
        label = f"multi_material.regions[{i}]"
        if not isinstance(region, dict):
            errors.append(f"{label} must be a mapping")
            continue
        identity = region.get("id")
        if not _text(identity) or identity in seen:
            errors.append(f"{label}: missing or duplicate region id")
        else:
            seen.add(identity)
        if not isinstance(region.get("body"), str) or region["body"] not in bodies:
            errors.append(f"{label}: unknown body")
        material = region.get("material")
        if not isinstance(material, str) or material not in by_id:
            errors.append(f"{label}: unknown material")
        else:
            used.add(material)
            if by_id[material].get("type") in SUPPORT_TYPES:
                errors.append(f"{label}: support material cannot be a model region")
        path = region.get("path")
        if not _relative(path) or not path.lower().endswith(".stl"):
            errors.append(f"{label}.path must be a project-relative STL")
        elif path in region_paths:
            errors.append(f"{label}: duplicate region/composite STL path")
        else:
            paths.append(path)
            region_paths.add(path)
        shells = region.get("expected_shells")
        if not isinstance(shells, int) or isinstance(shells, bool) or shells < 1:
            errors.append(f"{label}.expected_shells must be an integer >= 1")
        wall = region.get("min_wall_mm", data["manufacturing"]["nozzle_mm"] * 2)
        if not _number(wall) or wall < data["manufacturing"]["nozzle_mm"] * 2:
            errors.append(f"{label}.min_wall_mm must be at least two nozzle widths")

    region_bodies = {r.get("body") for r in regions if isinstance(r, dict) and isinstance(r.get("body"), str)}
    for name, body in bodies.items():
        material = body.get("material", primary)
        if not isinstance(material, str) or material not in by_id:
            errors.append(f"body {name}: unknown material")
        elif name not in region_bodies:
            used.add(material)
            if by_id[material]["type"] in SUPPORT_TYPES:
                errors.append(f"body {name}: support material cannot be a model body")
        if name in region_bodies and "material" in body:
            errors.append(f"body {name}: assign materials to its regions instead of the composite")

    interface = block.get("interface_material")
    if mode == "support-interface":
        if (not isinstance(interface, str) or interface not in by_id
                or by_id[interface].get("type") not in SUPPORT_TYPES):
            errors.append("interface_material must reference a dedicated support material")
        else:
            used.add(interface)
        if isinstance(primary, str) and primary in by_id and by_id[primary].get("type") not in ("PLA", "PETG"):
            errors.append("support-interface currently supports PLA/PETG model materials")
        if data["print"]["supports"] == "none":
            errors.append("support-interface requires a supports policy")
    elif interface is not None:
        errors.append("interface_material requires support-interface mode")
    for identity in by_id.keys() - used:
        errors.append(f"unused material: {identity}")
    types = {m.get("type") for m in by_id.values() if isinstance(m.get("type"), str)}
    if mode == "color" and (len(types) != 1 or types & SUPPORT_TYPES):
        errors.append("color mode requires one polymer type and different color assignments")
    if mode != "support-interface" and types & SUPPORT_TYPES:
        errors.append("dedicated support materials require support-interface mode")
    if mode == "support-interface" and len(types - SUPPORT_TYPES) != 1:
        errors.append("support-interface model regions must use one polymer type; functional pairs need bond_test")
    if mode == "functional":
        bond = block.get("bond_test")
        if (not isinstance(bond, dict) or bond.get("source") not in ("measured", "fit-tested")
                or not _relative(bond.get("report"))):
            errors.append("functional mode requires bond_test source measured/fit-tested and a project-relative report")
        else:
            paths.append(bond["report"])
    if data["service"]["environment"] == "wet":
        model_types = types - SUPPORT_TYPES
        if "PLA" in model_types:
            errors.append("wet service cannot use PLA model regions")
    if check_files and project is not None:
        errors.extend(f"declared file does not exist: {path}" for path in paths if not (project / path).is_file())
    return errors


def parse_material_plan(data: dict) -> MaterialPlan | None:
    block = data.get("multi_material")
    if block is None:
        return None
    return MaterialPlan(
        mode=block["mode"], reason=block["reason"], primary=block["primary"],
        bed_temperature_c=float(block["bed_temperature_c"]),
        materials=tuple(Material(m["id"], m["type"], m["profile"], m["color"],
                                 tuple(m["nozzle_temperature_c"]), tuple(m["bed_temperature_c"]))
                        for m in block["materials"]),
        regions=tuple(MaterialRegion(r["id"], r["body"], r["path"], r["material"],
                                     r["expected_shells"], float(r.get("min_wall_mm", data["manufacturing"]["nozzle_mm"] * 2)))
                      for r in block.get("regions", [])),
        interface_material=block.get("interface_material"),
        bond_report=block["bond_test"].get("report") if isinstance(block.get("bond_test"), dict) else None,
    )
