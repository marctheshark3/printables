from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from cad_pack import study_from_dump  # noqa: E402
from render_cad_project import build_html, find_steps, main  # noqa: E402
from test_cad_pack import box_dump  # noqa: E402


def test_find_steps_refuses_stl_only(tmp_path):
    (tmp_path / "out.stl").write_bytes(b"solid x\nendsolid x\n")
    with pytest.raises(Exception, match="mesh-only|No STEP"):
        find_steps(tmp_path, None)


def test_find_steps_picks_step(tmp_path):
    step_dir = tmp_path / "step"
    step_dir.mkdir()
    p = step_dir / "part.step"
    p.write_text("ISO-10303-21;")
    assert find_steps(tmp_path, None) == [p]


def test_cli_scene_builds_html(tmp_path, monkeypatch):
    bundle = ROOT / "viewer" / "viewer.bundle.js"
    if not bundle.is_file():
        pytest.skip("viewer.bundle.js not built yet")
    scene = tmp_path / "scene.json"
    scene.write_text(json.dumps(box_dump()))
    out = tmp_path / "inspector"
    rc = main(["--scene", str(scene), "--out-dir", str(out), "--title", "Box"])
    assert rc == 0
    html = (out / "viewer.html").read_text()
    assert "box" in html
    assert "brep-edges" in html
    assert "Orthographic" in html
    assert '<script id="study-data" type="application/json">/* STUDY_DATA */</script>' not in html
    assert '"instance":"box"' in html or '"instance": "box"' in html


def test_cli_rejects_public_bind(tmp_path):
    scene = tmp_path / "scene.json"
    scene.write_text(json.dumps(box_dump()))
    rc = main(["--scene", str(scene), "--out-dir", str(tmp_path / "o"), "--bind", "0.0.0.0"])
    assert rc == 2


def test_mapped_print_spec_step(tmp_path):
    docs = tmp_path / "docs"
    docs.mkdir()
    exports = tmp_path / "exports"
    exports.mkdir()
    step = exports / "widget.step"
    step.write_text("ISO-10303-21;")
    (docs / "PRINT_SPEC.yaml").write_text(
        "reverse:\n  step_files:\n    - path: exports/widget.step\n      body: widget\n"
    )
    assert find_steps(tmp_path, None) == [step]


def test_spec_step_rels_rejects_parent(tmp_path):
    docs = tmp_path / "docs"
    docs.mkdir()
    spec = "reverse:\n  step_files:\n    - path: ../secret.step\n"
    (docs / "PRINT_SPEC.yaml").write_text(spec)
    from render_cad_project import spec_step_rels

    assert spec_step_rels(spec) == []
    with pytest.raises(Exception, match="No STEP"):
        find_steps(tmp_path, None)


def test_title_is_html_escaped(tmp_path):
    study = study_from_dump(box_dump(), title="</title><script>alert(1)</script>")
    html = build_html(study, tmp_path / "out").read_text()
    assert "</title><script>" not in html
    assert "&lt;/title&gt;&lt;script&gt;" in html
