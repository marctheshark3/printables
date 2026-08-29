"""Deterministic reverse IR JSON (schema_version 1)."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

SCHEMA_VERSION = 1
IR_FLOAT_DECIMALS = 6

IR_KEY_ORDER = [
    "schema_version",
    "units",
    "input_stl",
    "body",
    "class",
    "alignment",
    "tolerance",
    "topology",
    "aabb_mm",
    "dimensions",
    "sketches",
    "features",
    "regions",
    "region_list",
    "mixed",
    "forbidden",
    "warnings",
    "open_mesh_forced",
    "expected_shells",
    "input_triangles",
]


def r6(value: float) -> float:
    return float(f"{float(value):.{IR_FLOAT_DECIMALS}f}")


def r6_list(values: Any) -> Any:
    if isinstance(values, (list, tuple)):
        return [r6_list(v) for v in values]
    if isinstance(values, float):
        return r6(values)
    return values


def empty_regions() -> dict[str, int]:
    return {
        "plane": 0,
        "cylinder": 0,
        "cone": 0,
        "sphere": 0,
        "torus": 0,
        "fillet": 0,
        "freeform_triangles": 0,
        "fallback": 0,
    }


def new_ir(*, input_stl: str, body: str, units: str = "mm") -> dict[str, Any]:
    return {
        "schema_version": SCHEMA_VERSION,
        "units": units,
        "input_stl": input_stl,
        "body": body,
        "class": "failed",
        "alignment": {
            "method": "pca-aabb",
            "translation_mm": [0.0, 0.0, 0.0],
            "rotation_rpy_deg": [0.0, 0.0, 0.0],
        },
        "tolerance": {
            "fit_mm": 0.05,
            "max_deviation_mm": 0.2,
            "snap_mm": None,
        },
        "topology": {},
        "aabb_mm": {"min": [0.0, 0.0, 0.0], "max": [0.0, 0.0, 0.0]},
        "dimensions": [],
        "sketches": [],
        "features": [],
        "regions": empty_regions(),
        "region_list": [],
        "mixed": [],
        "forbidden": {"triangle_wrapped_step": True},
        "warnings": [],
        "open_mesh_forced": False,
        "expected_shells": 1,
        "input_triangles": 0,
    }


def _encode(obj: Any, level: int) -> str:
    pad = "  " * level
    inner = "  " * (level + 1)
    if obj is None:
        return "null"
    if isinstance(obj, bool):
        return "true" if obj else "false"
    if isinstance(obj, int) and not isinstance(obj, bool):
        return str(obj)
    if isinstance(obj, float):
        return f"{obj:.{IR_FLOAT_DECIMALS}f}"
    if isinstance(obj, str):
        return json.dumps(obj, ensure_ascii=False)
    if isinstance(obj, (list, tuple)):
        if not obj:
            return "[]"
        parts = [inner + _encode(item, level + 1) for item in obj]
        return "[\n" + ",\n".join(parts) + "\n" + pad + "]"
    if isinstance(obj, dict):
        if not obj:
            return "{}"
        keys = [k for k in IR_KEY_ORDER if k in obj]
        keys.extend(k for k in obj.keys() if k not in keys)
        parts = []
        for key in keys:
            parts.append(f"{inner}{json.dumps(key)}: {_encode(obj[key], level + 1)}")
        return "{\n" + ",\n".join(parts) + "\n" + pad + "}"
    return json.dumps(obj, ensure_ascii=False)


def dumps_ir(ir: dict[str, Any]) -> str:
    return _encode(ir, 0) + "\n"


def public_ir(ir: dict[str, Any]) -> dict[str, Any]:
    return {k: v for k, v in ir.items() if not str(k).startswith("_")}


def write_ir(path: Path, ir: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(dumps_ir(public_ir(ir)), encoding="utf-8")


def load_ir(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"IR is not an object: {path}")
    if data.get("schema_version") != SCHEMA_VERSION:
        raise ValueError(f"IR schema_version must be {SCHEMA_VERSION}")
    return data


def ir_path(project: Path, body: str) -> Path:
    return project / "reverse" / f"{body}.ir.json"
