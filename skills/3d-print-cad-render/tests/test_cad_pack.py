from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from cad_pack import CadPackError, study_from_dump, validate_dump  # noqa: E402


def box_dump():
    # Unit cube: 8 verts, 12 tris, 12 BREP edges as 1-segment lines
    verts = [
        [0, 0, 0], [10, 0, 0], [10, 8, 0], [0, 8, 0],
        [0, 0, 6], [10, 0, 6], [10, 8, 6], [0, 8, 6],
    ]
    tris = [
        [0, 1, 2], [0, 2, 3],
        [4, 6, 5], [4, 7, 6],
        [0, 5, 1], [0, 4, 5],
        [3, 2, 6], [3, 6, 7],
        [1, 5, 6], [1, 6, 2],
        [0, 3, 7], [0, 7, 4],
    ]
    edges = [
        [[0, 0, 0], [10, 0, 0]], [[10, 0, 0], [10, 8, 0]], [[10, 8, 0], [0, 8, 0]], [[0, 8, 0], [0, 0, 0]],
        [[0, 0, 6], [10, 0, 6]], [[10, 0, 6], [10, 8, 6]], [[10, 8, 6], [0, 8, 6]], [[0, 8, 6], [0, 0, 6]],
        [[0, 0, 0], [0, 0, 6]], [[10, 0, 0], [10, 0, 6]], [[10, 8, 0], [10, 8, 6]], [[0, 8, 0], [0, 8, 6]],
    ]
    return {
        "source": "occ-step",
        "step": "box.step",
        "deflection_mm": 0.15,
        "parts": [{
            "id": "box",
            "instance": "box",
            "kind": "printed",
            "vertices": verts,
            "triangles": tris,
            "edges": edges,
            "bbox_mm": [10, 8, 6],
            "status": "cad",
            "evidence": "fixture",
        }],
    }


def test_validate_ok():
    validate_dump(box_dump())


def test_refuse_mesh_source():
    dump = box_dump()
    dump["source"] = "stl-mesh"
    with pytest.raises(CadPackError, match="occ-step"):
        validate_dump(dump)


def test_refuse_no_edges():
    dump = box_dump()
    dump["parts"][0]["edges"] = []
    with pytest.raises(CadPackError, match="BREP edges"):
        validate_dump(dump)


def test_study_has_cad_edge_keys():
    study = study_from_dump(box_dump(), title="Box")
    item = study["concepts"][0]["items"][0]
    assert item["cad_edges"]
    assert study["geometry"][item["cad_edges"]]["kind"] == "brep-edges"
    assert study["geometry"][item["geometry"]]["kind"] == "faces"
    assert "solid" in study["concepts"][0]["views"]
