from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from cad_catalog import CadPackError, build_shell, register_study, require_id, subset_study  # noqa: E402
from cad_pack import study_from_dump  # noqa: E402
from test_cad_pack import box_dump  # noqa: E402


def test_require_id_rejects_traversal():
    with pytest.raises(CadPackError, match="bad model id"):
        require_id("../viewer")
    with pytest.raises(CadPackError, match="bad model id"):
        require_id("STS_Yaw")


def test_register_and_subset(tmp_path):
    study = study_from_dump(box_dump(), title="Box")
    assert study["concepts"][0]["height"] == 6.0
    register_study(tmp_path, study, "box", name="Box")
    catalog = json.loads((tmp_path / "catalog.json").read_text())
    assert catalog["models"][0]["id"] == "box"
    payload = json.loads((tmp_path / "models" / "box.json").read_text())
    assert payload["concepts"][0]["items"][0]["instance"] == "box"
    lid = subset_study(payload, model_id="box-lid", name="Box lid", predicate=lambda it: it["instance"] == "box")
    register_study(tmp_path, lid, "box-lid", name="Box lid")
    catalog = json.loads((tmp_path / "catalog.json").read_text())
    assert [m["id"] for m in catalog["models"]] == ["box", "box-lid"]


def test_paths_reject_traversal_and_stick(tmp_path):
    study = study_from_dump(box_dump(), title="Box")
    register_study(tmp_path, study, "box", name="Box", path="yaw/assembly")
    from cad_catalog import require_path, set_paths
    with pytest.raises(CadPackError, match="bad model path"):
        require_path("../secret")
    with pytest.raises(CadPackError, match="bad model path"):
        require_path("Yaw/Base")
    set_paths(tmp_path, {"box": "assembly/base"})
    catalog = json.loads((tmp_path / "catalog.json").read_text())
    assert catalog["models"][0]["path"] == "assembly/base"
    with pytest.raises(CadPackError, match="bad model path"):
        set_paths(tmp_path, {"box": "../secret"})
    catalog = json.loads((tmp_path / "catalog.json").read_text())
    assert catalog["models"][0]["path"] == "assembly/base"
    bundle = ROOT / "viewer" / "viewer.bundle.js"
    if "catalog.json" not in bundle.read_text():
        pytest.skip("viewer.bundle.js not rebuilt")
    html = build_shell(tmp_path).read_text()
    assert 'id="model-tree"' in html
    assert "#c42b23" in html
    assert "#171714" in html
    assert "catalog.json" in html
    assert '<script id="study-data" type="application/json">null</script>' in html
