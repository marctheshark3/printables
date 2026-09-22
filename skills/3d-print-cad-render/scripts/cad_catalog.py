#!/usr/bin/env python3
"""Multi-model catalog for the Rage CAD inspector.

One shell (viewer.html) plus models/<id>.json. The page fetches the
selected study. Does not embed every STEP into one HTML.
"""
from __future__ import annotations

import json
import re
from html import escape
from pathlib import Path

from cad_pack import CadPackError

PATH_SEG = re.compile(r"^[a-z0-9][a-z0-9-]{0,63}$")
MODEL_ID = PATH_SEG
SKILL_DIR = Path(__file__).resolve().parents[1]
TEMPLATE = SKILL_DIR / "viewer" / "viewer.template.html"
BUNDLE = SKILL_DIR / "viewer" / "viewer.bundle.js"


def require_id(model_id: str) -> str:
    if not isinstance(model_id, str) or not MODEL_ID.match(model_id):
        raise CadPackError(f"bad model id: {model_id!r}")
    return model_id


def require_path(path: str) -> str:
    """Folder/file path. Segments match model ids. No traversal."""
    if not isinstance(path, str) or "/" not in path and not PATH_SEG.match(path):
        raise CadPackError(f"bad model path: {path!r}")
    parts = path.split("/")
    if not 1 <= len(parts) <= 6 or any(not PATH_SEG.match(part) for part in parts):
        raise CadPackError(f"bad model path: {path!r}")
    return path


def subset_study(study: dict, *, model_id: str, name: str, predicate) -> dict:
    """Copy one study down to the solids predicate keeps. Geometry keys are shared, not recomputed."""
    require_id(model_id)
    concepts = study.get("concepts") or []
    if not concepts:
        raise CadPackError("study has no concepts")
    items = [it for it in concepts[0].get("items") or [] if predicate(it)]
    if not items:
        raise CadPackError(f"subset {model_id} is empty")
    keys = set()
    for it in items:
        keys.add(it["geometry"])
        if it.get("cad_edges"):
            keys.add(it["cad_edges"])
    missing = [k for k in keys if k not in study.get("geometry", {})]
    if missing:
        raise CadPackError(f"subset {model_id} missing geometry {missing[0]}")
    width = max(float(it["bbox_mm"][0]) for it in items)
    depth = max(float(it["bbox_mm"][1]) for it in items)
    height = max(float(it["bbox_mm"][2]) for it in items)
    base = concepts[0]
    concept = {
        **{k: v for k, v in base.items() if k != "items"},
        "id": model_id,
        "name": name,
        "items": items,
        "width": round(width, 2),
        "depth": round(depth, 2),
        "height": round(height, 2),
        "metrics": {**base.get("metrics", {}), "solids": len(items), "source": name},
    }
    return {
        **study,
        "title": name,
        "concepts": [concept],
        "geometry": {k: study["geometry"][k] for k in keys},
        "step": name,
    }


def _load_catalog(path: Path) -> dict:
    if not path.is_file():
        return {"title": "Rage CAD inspector", "brand": "RAGE INDUSTRIES", "models": []}
    data = json.loads(path.read_text())
    if not isinstance(data, dict) or not isinstance(data.get("models"), list):
        raise CadPackError(f"catalog is not an object with models: {path}")
    return data


def register_study(root: Path, study: dict, model_id: str, *, name: str | None = None, path: str | None = None) -> Path:
    model_id = require_id(model_id)
    if not study.get("concepts") or not study["concepts"][0].get("items"):
        raise CadPackError(f"study {model_id} has no solids")
    root = root.resolve()
    models = root / "models"
    models.mkdir(parents=True, exist_ok=True)
    dest = models / f"{model_id}.json"
    payload = json.dumps(study, separators=(",", ":")).replace("<", "\\u003c")
    dest.write_text(payload)
    concept = study["concepts"][0]
    entry = {
        "id": model_id,
        "name": name or study.get("title") or model_id,
        "step": study.get("step") or "",
        "solids": len(concept["items"]),
        "envelope_mm": [
            concept.get("width"),
            concept.get("depth"),
            concept.get("height"),
        ],
    }
    catalog_path = root / "catalog.json"
    catalog = _load_catalog(catalog_path)
    previous = next((m for m in catalog["models"] if m.get("id") == model_id), None)
    if path:
        entry["path"] = require_path(path)
    elif previous and previous.get("path"):
        entry["path"] = require_path(previous["path"])
    catalog["title"] = catalog.get("title") or "Rage CAD inspector"
    catalog["brand"] = "RAGE INDUSTRIES"
    kept = [m for m in catalog["models"] if m.get("id") != model_id and require_id(m.get("id", ""))]
    kept.append(entry)
    kept.sort(key=lambda m: str(m.get("name", "")).lower())
    catalog["models"] = kept
    catalog_path.write_text(json.dumps(catalog, indent=2) + "\n")
    return dest


def set_default(root: Path, model_id: str) -> None:
    model_id = require_id(model_id)
    catalog_path = root / "catalog.json"
    catalog = _load_catalog(catalog_path)
    if not any(m.get("id") == model_id for m in catalog["models"]):
        raise CadPackError(f"default {model_id} is not in the catalog")
    catalog["default"] = model_id
    catalog_path.write_text(json.dumps(catalog, indent=2) + "\n")


def set_paths(root: Path, mapping: dict) -> None:
    """Attach folder/file paths. Keys are model ids. Does not move geometry files."""
    if not isinstance(mapping, dict) or not mapping:
        raise CadPackError("path map is empty")
    catalog_path = Path(root) / "catalog.json"
    catalog = _load_catalog(catalog_path)
    known = {m.get("id") for m in catalog["models"]}
    clean = {require_id(mid): require_path(path) for mid, path in mapping.items()}
    missing = [mid for mid in clean if mid not in known]
    if missing:
        raise CadPackError(f"path map names unknown model {missing[0]}")
    for entry in catalog["models"]:
        if entry["id"] in clean:
            entry["path"] = clean[entry["id"]]
    catalog["models"].sort(key=lambda m: (str(m.get("path") or m.get("name") or ""), str(m.get("name") or "")))
    catalog_path.write_text(json.dumps(catalog, indent=2) + "\n")


def build_shell(root: Path, *, title: str = "Rage CAD inspector") -> Path:
    """Write a shell viewer. Study geometry stays in models/*.json."""
    root = Path(root)
    if not TEMPLATE.is_file() or not BUNDLE.is_file():
        raise CadPackError(f"viewer template/bundle missing under {SKILL_DIR / 'viewer'}")
    runtime = BUNDLE.read_text().replace("</script", "<\\/script")
    html = (
        TEMPLATE.read_text()
        .replace("/* STUDY_DATA */", "null")
        .replace("/* VIEWER_RUNTIME */", runtime)
        .replace("<!-- TITLE -->", escape(title, quote=True))
        .replace("<!-- BRAND -->", escape("RAGE INDUSTRIES / CAD INSPECTOR", quote=True))
    )
    if "catalog.json" not in BUNDLE.read_text():
        raise CadPackError("viewer bundle has no catalog loader — rebuild viewer.bundle.js")
    root.mkdir(parents=True, exist_ok=True)
    out = root / "viewer.html"
    out.write_text(html)
    return out
