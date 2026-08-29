"""Emit/update docs/PRINT_SPEC.yaml from reverse IR."""
from __future__ import annotations

from pathlib import Path
from typing import Any

try:
    import yaml
except ImportError as exc:  # pragma: no cover
    raise SystemExit("HARD: PyYAML is required: python3 -m pip install PyYAML") from exc


def kernel_backend(kernel: str) -> str:
    if kernel == "cadquery":
        return "cadquery"
    return "vibecad"


def spec_from_ir(
    ir: dict[str, Any],
    *,
    kernel: str = "cadquery",
    part_name: str | None = None,
    product_class: str = "bracket",
) -> dict[str, Any]:
    body = ir.get("body") or "body"
    name = part_name or f"{body}-reverse"
    backend = kernel_backend(kernel)
    max_dev = float(ir.get("tolerance", {}).get("max_deviation_mm", 0.2))
    dims = []
    for d in ir.get("dimensions") or []:
        dims.append(
            {
                "name": d["name"],
                "parameter": d["parameter"],
                "value_mm": float(d["value_mm"]),
                "tolerance_mm": float(d.get("tolerance_mm", max_dev)),
                "source": d.get("source") or "measured",
            }
        )
    if not dims:
        dims = [
            {
                "name": "width",
                "parameter": "width_mm",
                "value_mm": 1.0,
                "tolerance_mm": max_dev,
                "source": "measured",
            }
        ]
    klass = ir.get("class") or "failed"
    if klass == "organic":
        backend = "blender"
    spec = {
        "schema_version": 1,
        "part": {
            "name": name,
            "revision": "0.1.0",
            "product_class": product_class,
            "purpose": f"Reverse-engineered {body} from reference STL (reconstruction, not conversion).",
        },
        "manufacturing": {
            "process": "fdm",
            "printer": "generic-256mm",
            "build_volume_mm": [256, 256, 256],
            "material": "PETG",
            "nozzle_mm": 0.4,
            "layer_height_mm": 0.2,
        },
        "cad": {
            "backend": backend,
            "parametric": True,
            "units": "mm",
            "source_files": [f"src/{body}.py"],
        },
        "geometry": {
            "min_wall_mm": 1.6,
            "min_feature_mm": 1.6,
            "overlapping_solids_allowed": False,
            "stl_files": [
                {
                    "path": f"stl/{body}.stl",
                    "body": body,
                    "expected_shells": int(ir.get("expected_shells") or 1),
                }
            ],
        },
        "fit": {
            "required": False,
            "clearance_per_side_mm": 0.4,
            "evidence": "none",
            "coupon": "not-required",
        },
        "dimensions": dims,
        "print": {
            "orientation": "base-on-bed",
            "bed_face": "bottom",
            "up_axis": "Z",
            "supports": "none",
            "max_overhang_deg": 45,
        },
        "service": {"environment": "dry", "drainage": "not-applicable"},
        "reverse": {
            "input_stl": ir.get("input_stl") or "source/original.stl",
            "ir": f"reverse/{body}.ir.json",
            "class": klass,
            "max_deviation_mm": max_dev,
        },
    }
    return spec


def write_print_spec(project: Path, spec: dict[str, Any]) -> Path:
    path = project / "docs" / "PRINT_SPEC.yaml"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.safe_dump(spec, sort_keys=False), encoding="utf-8")
    return path
