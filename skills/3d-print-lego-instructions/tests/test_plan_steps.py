from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

SKILL = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SKILL / "scripts"))

from plan_steps import ORDER_RULE, PlanError, plan_from_dump, plan_steps  # noqa: E402
from render_booklet import NOTE, booklet_html  # noqa: E402


def _box(name, origin, size=(10, 8, 6), color="#c4b49a"):
    ox, oy, oz = origin
    sx, sy, sz = size
    verts = [
        [ox, oy, oz], [ox + sx, oy, oz], [ox + sx, oy + sy, oz], [ox, oy + sy, oz],
        [ox, oy, oz + sz], [ox + sx, oy, oz + sz], [ox + sx, oy + sy, oz + sz], [ox, oy + sy, oz + sz],
    ]
    edges = [
        [verts[0], verts[1]], [verts[1], verts[2]], [verts[2], verts[3]], [verts[3], verts[0]],
        [verts[4], verts[5]], [verts[5], verts[6]], [verts[6], verts[7]], [verts[7], verts[4]],
        [verts[0], verts[4]], [verts[1], verts[5]], [verts[2], verts[6]], [verts[3], verts[7]],
    ]
    return {
        "id": name,
        "instance": name,
        "color": color,
        "vertices": verts,
        "edges": edges,
        "bbox_mm": [sx, sy, sz],
    }


def two_box_dump():
    return {
        "source": "occ-step",
        "step": "stack.step",
        "parts": [
            _box("cap", (0, 0, 6), size=(10, 8, 4)),
            _box("base", (0, 0, 0)),
        ],
    }


def test_order_is_bottom_up_then_name():
    steps = plan_from_dump(two_box_dump())
    assert [s["new_ids"] for s in steps] == [["base"], ["cap"]]
    assert steps[0]["placed_ids"] == ["base"]
    assert steps[1]["placed_ids"] == ["base", "cap"]
    assert ORDER_RULE == "centroid z, then y, then x, then name"


def test_name_breaks_a_centroid_tie():
    parts = [_box("b", (0, 0, 0), color="#111111"), _box("a", (0, 0, 0), color="#222222")]
    steps = plan_steps(parts)
    assert [s["new_ids"] for s in steps] == [["a"], ["b"]]


def test_same_fingerprint_in_band_is_one_step():
    parts = [_box("left", (0, 0, 0)), _box("right", (30, 0, 1))]
    steps = plan_steps(parts)
    assert len(steps) == 1
    assert steps[0]["quantity"] == 2
    assert steps[0]["new_ids"] == ["left", "right"]


def test_same_shape_above_the_band_is_a_new_step():
    parts = [_box("low", (0, 0, 0)), _box("high", (0, 0, 9))]
    steps = plan_steps(parts)
    assert [s["quantity"] for s in steps] == [1, 1]


def test_color_splits_a_group():
    parts = [_box("cream", (0, 0, 0)), _box("ink", (20, 0, 0), color="#1c1b18")]
    steps = plan_steps(parts)
    assert len(steps) == 2


def test_single_solid_is_one_sheet():
    dump = {"source": "occ-step", "step": "one.step", "parts": [_box("only", (0, 0, 0))]}
    steps = plan_from_dump(dump)
    assert len(steps) == 1
    assert steps[0]["new_ids"] == steps[0]["placed_ids"] == ["only"]


def test_refuse_mesh_and_empty():
    with pytest.raises(PlanError, match="occ-step"):
        plan_from_dump({"source": "stl-mesh", "parts": [_box("a", (0, 0, 0))]})
    with pytest.raises(PlanError, match="empty"):
        plan_steps([])


def test_booklet_hides_later_solids_and_escapes():
    html_text = booklet_html(two_box_dump(), title="</title><script>alert(1)</script>")
    assert "centroid z, then y, then x, then name" in html_text
    assert "Not an LDraw" in html_text
    assert NOTE in html_text
    assert "<script>alert" not in html_text
    assert "&lt;script&gt;" in html_text
    step1 = html_text.split('data-step="1"', 1)[1].split('data-step="2"', 1)[0]
    step2 = html_text.split('data-step="2"', 1)[1]
    assert step1.count("<path") == 2  # CSI new + PLI
    assert 'stroke="#c42b23"' in step1
    assert step2.count('stroke="#1c1b18"') >= 1
    assert "1×" in step1
    assert 'data-role="bom"' in html_text


def test_cli_writes_html_and_refuses_mesh(tmp_path):
    scene = tmp_path / "scene.json"
    scene.write_text(json.dumps(two_box_dump()), encoding="utf-8")
    out = tmp_path / "nested" / "instructions.html"
    script = SKILL / "scripts" / "render_booklet.py"
    proc = subprocess.run(
        [sys.executable, str(script), str(scene), "--out", str(out), "--title", "Stack"],
        check=False, capture_output=True, text=True,
    )
    assert proc.returncode == 0, proc.stderr
    assert "Stack" in out.read_text(encoding="utf-8")
    bad = dict(two_box_dump())
    bad["source"] = "stl-mesh"
    scene.write_text(json.dumps(bad), encoding="utf-8")
    refused = subprocess.run(
        [sys.executable, str(script), str(scene), "--out", str(tmp_path / "no.html")],
        check=False, capture_output=True, text=True,
    )
    assert refused.returncode == 1
    assert "occ-step" in refused.stderr


def test_viewer_button_uses_the_same_rule():
    viewer = SKILL.parent / "3d-print-cad-render" / "viewer"
    js = (viewer / "instructions.js").read_text(encoding="utf-8")
    app = (viewer / "app.js").read_text(encoding="utf-8")
    html_text = (viewer / "viewer.template.html").read_text(encoding="utf-8")
    assert ORDER_RULE in js
    assert "Z_BAND_MM = 2" in js
    assert "instructions.js" in app
    assert 'id="instructions"' in html_text
    bundle = (viewer / "viewer.bundle.js").read_text(encoding="utf-8")
    assert ORDER_RULE in bundle
    assert "#instructions" in bundle
