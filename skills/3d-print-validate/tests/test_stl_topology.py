from __future__ import annotations

import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "validate_stl.py"
spec = importlib.util.spec_from_file_location("dfm_gate", SCRIPT)
assert spec and spec.loader
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


def tetra(offset=(0.0, 0.0, 0.0)):
    ox, oy, oz = offset
    a = (ox + 0.0, oy + 0.0, oz + 0.0)
    b = (ox + 1.0, oy + 0.0, oz + 0.0)
    c = (ox + 0.0, oy + 1.0, oz + 0.0)
    d = (ox + 0.0, oy + 0.0, oz + 1.0)
    return [(a, c, b), (a, b, d), (a, d, c), (b, c, d)]


def test_closed_tetra_is_one_watertight_component():
    result = module.topology_metrics(tetra(), 1e-6)
    assert result["boundary_edges"] == 0
    assert result["nonmanifold_edges"] == 0
    assert result["orientation_edges"] == 0
    assert result["duplicate_faces"] == 0
    assert result["components"] == 1


def test_open_mesh_has_boundary_edges():
    result = module.topology_metrics(tetra()[:-1], 1e-6)
    assert result["boundary_edges"] == 3


def test_disconnected_shells_are_counted():
    result = module.topology_metrics(tetra() + tetra((3.0, 0.0, 0.0)), 1e-6)
    assert result["components"] == 2
    assert result["boundary_edges"] == 0


def test_duplicate_face_is_rejected_signal():
    faces = tetra()
    result = module.topology_metrics(faces + [faces[0]], 1e-6)
    assert result["duplicate_faces"] == 1
    assert result["nonmanifold_edges"] == 3


def test_inconsistent_orientation_is_detected():
    faces = tetra()
    a, b, c = faces[0]
    faces[0] = (a, c, b)
    result = module.topology_metrics(faces, 1e-6)
    assert result["orientation_edges"] == 3
