#!/usr/bin/env python3
"""dfm_gate.py — hard manufacturing checks for printables STLs.

Pure stdlib + optional numpy. No trimesh required.

Usage:
  dfm_gate.py --project DIR --stl path.stl [--mode-file docs/DESIGN.md]
  dfm_gate.py --stl path.stl --product-class equipment-open-frame --print-orientation TOP-FIRST

Exit 0 = no HARD fails. Exit 1 = HARD fail(s).
"""
from __future__ import annotations

import argparse
import math
import re
import struct
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Printables DFM mesh/mode gates")
    p.add_argument("--project", type=Path, default=None, help="Project root")
    p.add_argument("--stl", type=Path, required=True, help="Binary STL path")
    p.add_argument("--mode-file", type=Path, default=None, help="DESIGN.md path")
    p.add_argument("--product-class", default=None)
    p.add_argument("--print-orientation", default=None)
    p.add_argument("--print-up-axis", default=None, choices=["X", "Y", "Z", "x", "y", "z"])
    p.add_argument("--min-feature-mm", type=float, default=None)
    p.add_argument("--overhang-max-deg", type=float, default=None)
    p.add_argument("--overhang-fail-area-frac", type=float, default=0.28,
                    help="HARD if fraction of *unsupported* face area beyond overhang exceeds this "
                         "(coarse mesh heuristic; open frames often ~0.15–0.25)")
    p.add_argument("--bed-support-mm", type=float, default=1.6,
                    help="Exclude faces with centroid within this distance of the bed plane from overhang")
    p.add_argument("--thin-edge-mm", type=float, default=0.5)
    p.add_argument("--thin-fail-frac", type=float, default=0.35,
                    help="Legacy name: WARN when many mesh edges are below the chord threshold")
    p.add_argument("--open-under-solid-frac", type=float, default=0.22,
                    help="HARD for equipment-open-frame if under-deck solid frac above this")
    p.add_argument("--expected-components", type=int, default=None,
                    help="Expected edge-connected closed shells (defaults to mode file or 1)")
    p.add_argument("--weld-tolerance-mm", type=float, default=1e-5,
                    help="Vertex weld tolerance used by topology checks")
    p.add_argument("--build-x-mm", type=float, required=True)
    p.add_argument("--build-y-mm", type=float, required=True)
    p.add_argument("--build-z-mm", type=float, required=True)
    p.add_argument("--skip-overhang", action="store_true")
    p.add_argument("--skip-open-under", action="store_true")
    p.add_argument("--json-summary", action="store_true")
    return p.parse_args()


def read_mode_file(path: Path) -> Dict[str, str]:
    """Parse simple key: value from YAML frontmatter and/or body labels."""
    if not path or not path.is_file():
        return {}
    text = path.read_text(encoding="utf-8", errors="replace")
    out: Dict[str, str] = {}

    # YAML frontmatter
    if text.startswith("---"):
        end = text.find("\n---", 3)
        if end != -1:
            fm = text[3:end]
            for line in fm.splitlines():
                m = re.match(r"^([A-Za-z0-9_]+)\s*:\s*(.+)$", line.strip())
                if m:
                    out[m.group(1).lower()] = m.group(2).strip().strip('"').strip("'")

    # Body fallbacks
    patterns = {
        "product_class": r"product[_\s-]?class\s*[:=]\s*`?([a-z0-9_-]+)`?",
        "print_orientation": r"print[_\s-]?orientation\s*[:=]\s*`?([A-Za-z0-9_-]+)`?",
        "print_up_axis": r"print[_\s-]?up[_\s-]?axis\s*[:=]\s*`?([XYZ])`?",
        "min_feature_mm": r"min[_\s-]?feature(?:_mm)?\s*[:=]\s*`?([0-9.]+)`?",
        "overhang_max_deg": r"overhang[_\s-]?(?:max_)?(?:deg)?\s*[:=]\s*`?([0-9.]+)`?",
        "clearance_mm": r"clearance(?:_mm)?\s*[:=]\s*`?([0-9.]+)`?",
        "expected_components": r"expected[_\s-]?components\s*[:=]\s*([0-9]+)",
        "fit_required": r"fit[_\s-]?required\s*[:=]\s*([A-Za-z0-9_-]+)",
        "critical_fit_status": r"critical[_\s-]?fit[_\s-]?status\s*[:=]\s*([A-Za-z0-9_-]+)",
        "service_environment": r"service[_\s-]?environment\s*[:=]\s*([A-Za-z0-9_-]+)",
        "drainage": r"drainage\s*[:=]\s*([A-Za-z0-9_-]+)",
        "material": r"material\s*[:=]\s*([A-Za-z0-9_-]+)",
        "gate_override": r"gate[_\s-]?override\s*[:=]\s*(.+)$",
    }
    for key, pat in patterns.items():
        if key in out:
            continue
        m = re.search(pat, text, re.I | re.M)
        if m:
            out[key] = m.group(1).strip()

    # TOP-FIRST language → orientation
    if "print_orientation" not in out:
        if re.search(r"TOP-FIRST|top[\s-]?first", text, re.I):
            out["print_orientation"] = "TOP-FIRST"
        elif re.search(r"feet[\s-]?down", text, re.I):
            out["print_orientation"] = "feet-down"

    if "product_class" not in out:
        if re.search(r"open[\s-]?frame|equipment-open-frame", text, re.I):
            out["product_class"] = "equipment-open-frame"
        elif re.search(r"\btray\b", text, re.I):
            out["product_class"] = "tray"
        elif re.search(r"\bbracket\b", text, re.I):
            out["product_class"] = "bracket"

    return out


def load_binary_stl(path: Path) -> Tuple[Any, Any, Any]:
    """Return (vertices Nx3, faces Mx3 indices into unique verts is expensive —
    instead return triangle arrays: v0,v1,v2 each Mx3 float)."""
    data = path.read_bytes()
    if len(data) < 84:
        raise ValueError("STL too small")
    n = struct.unpack_from("<I", data, 80)[0]
    expected = 84 + n * 50
    if n <= 0 or n > 50_000_000 or expected > len(data) + 50:
        # Maybe ASCII
        if data[:5].lower() == b"solid" and b"facet" in data[:2000].lower():
            return load_ascii_stl(data.decode("utf-8", errors="replace"))
        raise ValueError(f"Not a binary STL or triangle count absurd: n={n}")

    import array

    # Store as flat lists then reshape with simple python structures
    tris: List[Tuple[Tuple[float, float, float], Tuple[float, float, float], Tuple[float, float, float]]] = []
    normals: List[Tuple[float, float, float]] = []
    off = 84
    for _ in range(n):
        nx, ny, nz, x1, y1, z1, x2, y2, z2, x3, y3, z3 = struct.unpack_from("<12f", data, off)
        off += 50
        normals.append((nx, ny, nz))
        tris.append(((x1, y1, z1), (x2, y2, z2), (x3, y3, z3)))
    return normals, tris, n


def load_ascii_stl(text: str):
    normals = []
    tris = []
    cur_n = (0.0, 0.0, 1.0)
    verts: List[Tuple[float, float, float]] = []
    for line in text.splitlines():
        parts = line.strip().split()
        if not parts:
            continue
        if parts[0] == "facet" and len(parts) >= 5 and parts[1] == "normal":
            cur_n = (float(parts[2]), float(parts[3]), float(parts[4]))
            verts = []
        elif parts[0] == "vertex" and len(parts) >= 4:
            verts.append((float(parts[1]), float(parts[2]), float(parts[3])))
        elif parts[0] == "endfacet" and len(verts) >= 3:
            normals.append(cur_n)
            tris.append((verts[0], verts[1], verts[2]))
    return normals, tris, len(tris)


def tri_area(a, b, c) -> float:
    ab = (b[0] - a[0], b[1] - a[1], b[2] - a[2])
    ac = (c[0] - a[0], c[1] - a[1], c[2] - a[2])
    cx = ab[1] * ac[2] - ab[2] * ac[1]
    cy = ab[2] * ac[0] - ab[0] * ac[2]
    cz = ab[0] * ac[1] - ab[1] * ac[0]
    return 0.5 * math.sqrt(cx * cx + cy * cy + cz * cz)


def tri_normal(a, b, c):
    ab = (b[0] - a[0], b[1] - a[1], b[2] - a[2])
    ac = (c[0] - a[0], c[1] - a[1], c[2] - a[2])
    nx = ab[1] * ac[2] - ab[2] * ac[1]
    ny = ab[2] * ac[0] - ab[0] * ac[2]
    nz = ab[0] * ac[1] - ab[1] * ac[0]
    L = math.sqrt(nx * nx + ny * ny + nz * nz) or 1.0
    return (nx / L, ny / L, nz / L)


def bbox_and_volume(tris) -> Tuple[List[float], List[float], float]:
    mn = [1e30, 1e30, 1e30]
    mx = [-1e30, -1e30, -1e30]
    vol = 0.0
    for a, b, c in tris:
        for p in (a, b, c):
            for i in range(3):
                if p[i] < mn[i]:
                    mn[i] = p[i]
                if p[i] > mx[i]:
                    mx[i] = p[i]
        x1, y1, z1 = a
        x2, y2, z2 = b
        x3, y3, z3 = c
        vol += (
            x1 * (y2 * z3 - y3 * z2)
            - y1 * (x2 * z3 - x3 * z2)
            + z1 * (x2 * y3 - x3 * y2)
        ) / 6.0
    return mn, mx, abs(vol)


def topology_metrics(tris, weld_tolerance: float) -> Dict[str, int]:
    """Weld STL vertices, then audit the triangle surface as an edge graph."""
    if weld_tolerance <= 0:
        raise ValueError("weld tolerance must be positive")

    vertex_ids: Dict[Tuple[int, int, int], int] = {}
    edge_uses: Dict[Tuple[int, int], List[Tuple[int, int, int]]] = {}
    face_uses: Dict[Tuple[int, int, int], int] = {}
    degenerate = 0
    active_triangles: List[int] = []

    def vertex_id(p) -> int:
        key = tuple(int(round(float(c) / weld_tolerance)) for c in p)
        if key not in vertex_ids:
            vertex_ids[key] = len(vertex_ids)
        return vertex_ids[key]

    parent = list(range(len(tris)))

    def find(i: int) -> int:
        while parent[i] != i:
            parent[i] = parent[parent[i]]
            i = parent[i]
        return i

    def union(a: int, b: int) -> None:
        ra, rb = find(a), find(b)
        if ra != rb:
            parent[rb] = ra

    for tri_index, (a, b, c) in enumerate(tris):
        ids = (vertex_id(a), vertex_id(b), vertex_id(c))
        if len(set(ids)) < 3 or tri_area(a, b, c) <= weld_tolerance * weld_tolerance:
            degenerate += 1
            continue
        active_triangles.append(tri_index)
        face_key = tuple(sorted(ids))
        face_uses[face_key] = face_uses.get(face_key, 0) + 1
        for u, v in ((ids[0], ids[1]), (ids[1], ids[2]), (ids[2], ids[0])):
            edge_key = (u, v) if u < v else (v, u)
            edge_uses.setdefault(edge_key, []).append((tri_index, u, v))

    boundary_edges = sum(1 for uses in edge_uses.values() if len(uses) == 1)
    nonmanifold_edges = sum(1 for uses in edge_uses.values() if len(uses) > 2)
    orientation_edges = 0
    for uses in edge_uses.values():
        if len(uses) == 2:
            _, u0, v0 = uses[0]
            _, u1, v1 = uses[1]
            if not (u0 == v1 and v0 == u1):
                orientation_edges += 1
        first = uses[0][0]
        for use in uses[1:]:
            union(first, use[0])

    components = len({find(i) for i in active_triangles}) if active_triangles else 0
    duplicate_faces = sum(count - 1 for count in face_uses.values() if count > 1)
    return {
        "vertices": len(vertex_ids),
        "edges": len(edge_uses),
        "boundary_edges": boundary_edges,
        "nonmanifold_edges": nonmanifold_edges,
        "orientation_edges": orientation_edges,
        "degenerate_faces": degenerate,
        "duplicate_faces": duplicate_faces,
        "components": components,
    }


def resolve_print_up(orientation: Optional[str], axis: Optional[str]) -> Tuple[float, float, float]:
    if axis:
        a = axis.upper()
        return {"X": (1, 0, 0), "Y": (0, 1, 0), "Z": (0, 0, 1)}[a]
    o = (orientation or "TOP-FIRST").upper().replace("_", "-")
    # STL coordinates: Z is typically part height; TOP-FIRST means rim on bed so
    # print-up is still +Z in model if model is authored print-oriented.
    # feet-down same axis assumption unless stated.
    if "X" in o and "UP" in o:
        return (1, 0, 0)
    if "Y" in o and "UP" in o:
        return (0, 1, 0)
    return (0, 0, 1)


def main() -> int:
    args = parse_args()
    project = args.project.resolve() if args.project else None
    stl = args.stl.expanduser()
    if project and not stl.is_absolute():
        stl = (project / stl).resolve()
    else:
        stl = stl.resolve()

    mode_path = args.mode_file
    if mode_path is None and project:
        cand = project / "docs" / "DESIGN.md"
        if cand.is_file():
            mode_path = cand
    mode = read_mode_file(mode_path) if mode_path else {}

    product_class = (args.product_class or mode.get("product_class") or "other").lower()
    print_orientation = args.print_orientation or mode.get("print_orientation")
    print_up_axis = args.print_up_axis or mode.get("print_up_axis")
    min_feature = args.min_feature_mm
    if min_feature is None:
        min_feature = float(mode.get("min_feature_mm") or 1.6)
    overhang_max = args.overhang_max_deg
    if overhang_max is None:
        overhang_max = float(mode.get("overhang_max_deg") or 45.0)
    expected_components = args.expected_components
    if expected_components is None:
        expected_components = int(mode.get("expected_components") or 1)
    fit_required = (mode.get("fit_required") or "no").lower()
    critical_fit_status = (mode.get("critical_fit_status") or "unspecified").lower()
    service_environment = (mode.get("service_environment") or "dry").lower()
    drainage = (mode.get("drainage") or "unspecified").lower()
    material = (mode.get("material") or "unspecified").lower()

    hard: List[str] = []
    warn: List[str] = []
    info: List[str] = []

    def hard_fail(msg: str) -> None:
        hard.append(msg)

    def soft_warn(msg: str) -> None:
        warn.append(msg)

    # G-mode
    if not product_class or product_class == "other":
        if not mode.get("product_class"):
            hard_fail("G-mode: missing product_class in DESIGN.md (set product_class: …)")
    if not print_orientation:
        hard_fail("G-mode: missing print_orientation in DESIGN.md")
    else:
        info.append(f"mode product_class={product_class} orientation={print_orientation}")
    info.append(f"expected_components={expected_components}")

    if fit_required in ("yes", "true", "required"):
        accepted_fit = ("measured", "fit-tested", "fit_tested", "from-user")
        if critical_fit_status not in accepted_fit:
            hard_fail(
                "G-fit: fit_required=yes but critical_fit_status is not measured, "
                "from-user, or fit-tested"
            )
    if service_environment in ("wet", "wet-service", "water"):
        info.append(f"wet_service drainage={drainage} material={material}")
        if drainage not in ("open-continuous", "open_continuous", "through-drain", "drainable"):
            hard_fail("G-wet: wet-service part must declare positive drainage")
        if material in ("pla", "unspecified"):
            hard_fail("G-wet: long-term wet part requires a declared wet-service material, not PLA")

    if not stl.is_file():
        hard_fail(f"G-stl: missing {stl}")
        _report(hard, warn, info, args.json_summary)
        return 1

    try:
        normals, tris, ntri = load_binary_stl(stl)
    except Exception as e:
        hard_fail(f"G-stl: parse failed: {e}")
        _report(hard, warn, info, args.json_summary)
        return 1

    if ntri < 4:
        hard_fail(f"G-stl: too few triangles ({ntri})")

    try:
        topo = topology_metrics(tris, args.weld_tolerance_mm)
        info.append(
            "topology "
            f"verts={topo['vertices']} edges={topo['edges']} "
            f"boundary={topo['boundary_edges']} nonmanifold={topo['nonmanifold_edges']} "
            f"orientation={topo['orientation_edges']} components={topo['components']}"
        )
        if topo["boundary_edges"]:
            hard_fail(f"G-topology: {topo['boundary_edges']} boundary edges; mesh is open")
        if topo["nonmanifold_edges"]:
            hard_fail(f"G-topology: {topo['nonmanifold_edges']} non-manifold edges")
        if topo["orientation_edges"]:
            hard_fail(f"G-topology: {topo['orientation_edges']} inconsistently oriented edges")
        degenerate_limit = max(2, int(ntri * 0.01))
        if topo["degenerate_faces"] > degenerate_limit:
            hard_fail(
                f"G-topology: {topo['degenerate_faces']} degenerate faces "
                f"exceed limit {degenerate_limit}"
            )
        elif topo["degenerate_faces"]:
            soft_warn(f"G-topology: {topo['degenerate_faces']} degenerate faces")
        if topo["duplicate_faces"]:
            hard_fail(f"G-topology: {topo['duplicate_faces']} duplicate faces")
        if topo["components"] != expected_components:
            hard_fail(
                f"G-components: expected {expected_components}, found {topo['components']} "
                "edge-connected shells"
            )
    except Exception as e:
        hard_fail(f"G-topology: audit failed: {e}")

    mn, mx, vol = bbox_and_volume(tris)
    dx, dy, dz = mx[0] - mn[0], mx[1] - mn[1], mx[2] - mn[2]
    cm3 = vol / 1000.0
    info.append(f"mesh tris={ntri} bbox={dx:.2f}x{dy:.2f}x{dz:.2f} mm vol={cm3:.2f} cm³")

    # Build-volume check in model XYZ. PRINT_SPEC locks Z-up.
    if dx > args.build_x_mm or dy > args.build_y_mm or dz > args.build_z_mm:
        hard_fail(
            f"G-build-volume: {dx:.1f}×{dy:.1f}×{dz:.1f} mm exceeds "
            f"{args.build_x_mm:.1f}×{args.build_y_mm:.1f}×{args.build_z_mm:.1f} mm"
        )

    up = resolve_print_up(print_orientation, print_up_axis)
    info.append(f"print_up={up}")

    # Open frames legitimately expose more downward faces (leg shoulders, deck thickness).
    # Prefer G-open-under as the product-class HARD gate; keep overhang as coarse support smell.
    overhang_limit = args.overhang_fail_area_frac
    if product_class in ("equipment-open-frame", "equipment_open_frame", "open-frame"):
        overhang_limit = max(overhang_limit, 0.30)

    # Overhang: faces whose outward normal points "downward" more than max angle
    # For FDM, surfaces with normal·up < cos(90+max) need support.
    # Angle from vertical: theta = acos(normal·up); overhang if theta > 90+? 
    # Standard: face needs support if angle between face normal and +Z is > 90+overhang
    # i.e. downward-facing steeper than overhang_max from horizontal.
    # cos(n·up) = n_z. Face is overhanging if n_z < -sin(overhang) roughly:
    # wall vertical: n_z=0; horizontal floor: n_z=-1; 45° overhang: n_z = -sin(45)= -0.707
    if not args.skip_overhang and tris:
        thr = -math.sin(math.radians(overhang_max))
        # Bed plane = minimum coordinate along print-up (part sitting on bed)
        bed = mn[0] * up[0] + mn[1] * up[1] + mn[2] * up[2]
        # For axis-aligned up, min component is correct; general case use projected min
        bed = min(p[0] * up[0] + p[1] * up[1] + p[2] * up[2] for tri in tris for p in tri)
        bad_area = 0.0
        tot_area = 0.0
        bed_excl = 0.0
        for i, (a, b, c) in enumerate(tris):
            area = tri_area(a, b, c)
            tot_area += area
            cz = (
                (a[0] + b[0] + c[0]) / 3.0 * up[0]
                + (a[1] + b[1] + c[1]) / 3.0 * up[1]
                + (a[2] + b[2] + c[2]) / 3.0 * up[2]
            )
            # Faces on the bed are supported — not manufacturing overhangs
            if cz <= bed + args.bed_support_mm:
                bed_excl += area
                continue
            n = normals[i] if i < len(normals) else tri_normal(a, b, c)
            if abs(n[0]) + abs(n[1]) + abs(n[2]) < 1e-9:
                n = tri_normal(a, b, c)
            nz = n[0] * up[0] + n[1] * up[1] + n[2] * up[2]
            if nz < thr:
                bad_area += area
        denom = max(tot_area - bed_excl, 1e-9)
        frac = bad_area / denom
        info.append(
            f"overhang unsupported_frac={frac:.3f} thr_n·up<{thr:.3f} "
            f"max_deg={overhang_max} bed_excl_frac={bed_excl/max(tot_area,1e-9):.3f}"
        )
        if frac > overhang_limit:
            hard_fail(
                f"G-overhang: {frac*100:.1f}% unsupported face area steeper than {overhang_max}° "
                f"(limit {overhang_limit*100:.0f}%) — reorient or add 45° structure"
            )
        elif frac > overhang_limit * 0.55:
            soft_warn(f"G-overhang: {frac*100:.1f}% unsupported area near overhang limit")

    # STL edge length is a tessellation-density signal, not a wall-thickness test.
    # Keep it warning-only; minimum wall must be verified in CAD or the slicer.
    if tris:
        edge_lens: List[float] = []
        step = max(1, ntri // 80000)
        for i in range(0, ntri, step):
            a, b, c = tris[i]
            for p, q in ((a, b), (b, c), (c, a)):
                d = math.sqrt(
                    (p[0] - q[0]) ** 2 + (p[1] - q[1]) ** 2 + (p[2] - q[2]) ** 2
                )
                if d > 1e-6:
                    edge_lens.append(d)
        if edge_lens:
            thin_thr = args.thin_edge_mm
            thin = sum(1 for L in edge_lens if L < thin_thr)
            frac = thin / len(edge_lens)
            info.append(
                f"thin_edges frac={frac:.3f} thr={thin_thr:.2f} mm "
                f"samples={len(edge_lens)} min_feature={min_feature}"
            )
            if frac > args.thin_fail_frac:
                soft_warn(
                    f"G-tessellation: {frac*100:.1f}% edges under {thin_thr:.2f} mm; "
                    f"short STL chords do not prove a thin wall. Verify CAD/slicer wall ≥ {min_feature} mm"
                )

    # Open-under: equipment-open-frame must be empty under the seating deck.
    # TOP-FIRST print: deck near min-Z (bed), feet at max-Z → open air is MID height.
    # feet-down: open air is also mid height between feet and deck.
    # Check interior XY cells in mid Z band — perimeter pillars are OK; waffle/pins fill interior.
    if (
        not args.skip_open_under
        and product_class in ("equipment-open-frame", "equipment_open_frame", "open-frame")
        and tris
        and dz > 5.0
    ):
        z0 = mn[2]
        # Start above typical seat/deck slab (TOP-FIRST decks live near min-Z).
        # 0.30*dz clears ~lip+flange; mid-high band is the empty-air volume.
        under_lo = z0 + 0.30 * dz
        under_hi = z0 + 0.82 * dz
        nxg, nyg = 28, 28
        cells = [[0 for _ in range(nyg)] for _ in range(nxg)]
        cell_w = max(dx, 1e-6) / nxg
        cell_h = max(dy, 1e-6) / nyg

        def point_in_tri_xy(px: float, py: float, a, b, c) -> bool:
            """Barycentric test in XY only (ignore Z)."""
            x1, y1 = a[0], a[1]
            x2, y2 = b[0], b[1]
            x3, y3 = c[0], c[1]
            den = (y2 - y3) * (x1 - x3) + (x3 - x2) * (y1 - y3)
            if abs(den) < 1e-12:
                return False
            w1 = ((y2 - y3) * (px - x3) + (x3 - x2) * (py - y3)) / den
            w2 = ((y3 - y1) * (px - x3) + (x1 - x3) * (py - y3)) / den
            w3 = 1.0 - w1 - w2
            return w1 >= -1e-6 and w2 >= -1e-6 and w3 >= -1e-6

        def z_at_xy(px: float, py: float, a, b, c) -> Optional[float]:
            """Interpolate Z on triangle plane at XY if inside."""
            x1, y1, z1 = a
            x2, y2, z2 = b
            x3, y3, z3 = c
            den = (y2 - y3) * (x1 - x3) + (x3 - x2) * (y1 - y3)
            if abs(den) < 1e-12:
                return None
            w1 = ((y2 - y3) * (px - x3) + (x3 - x2) * (py - y3)) / den
            w2 = ((y3 - y1) * (px - x3) + (x1 - x3) * (py - y3)) / den
            w3 = 1.0 - w1 - w2
            if w1 < -1e-6 or w2 < -1e-6 or w3 < -1e-6:
                return None
            return w1 * z1 + w2 * z2 + w3 * z3

        # Rasterize each triangle into XY cells; mark if plane Z is in mid band.
        # Catches large waffle tops (few triangles covering lots of area).
        for a, b, c in tris:
            xs = [a[0], b[0], c[0]]
            ys = [a[1], b[1], c[1]]
            min_x, max_x = min(xs), max(xs)
            min_y, max_y = min(ys), max(ys)
            ix0 = max(0, int((min_x - mn[0]) / max(dx, 1e-6) * nxg) - 1)
            ix1 = min(nxg - 1, int((max_x - mn[0]) / max(dx, 1e-6) * nxg) + 1)
            iy0 = max(0, int((min_y - mn[1]) / max(dy, 1e-6) * nyg) - 1)
            iy1 = min(nyg - 1, int((max_y - mn[1]) / max(dy, 1e-6) * nyg) + 1)
            for ix in range(ix0, ix1 + 1):
                for iy in range(iy0, iy1 + 1):
                    cx = mn[0] + (ix + 0.5) * cell_w
                    cy = mn[1] + (iy + 0.5) * cell_h
                    z = z_at_xy(cx, cy, a, b, c)
                    if z is None:
                        continue
                    if under_lo <= z <= under_hi:
                        cells[ix][iy] += 1
        # Interior only (skip 2-cell perimeter frame where legs live)
        margin = 3
        interior = 0
        filled_int = 0
        for ix in range(margin, nxg - margin):
            for iy in range(margin, nyg - margin):
                interior += 1
                if cells[ix][iy] > 0:
                    filled_int += 1
        frac = (filled_int / float(interior)) if interior else 0.0
        info.append(
            f"open_under interior_solid_frac={frac:.3f} "
            f"band_z=[{under_lo:.1f},{under_hi:.1f}]"
        )
        # Pins/waffle fill interior; open frame should be sparse.
        if frac > args.open_under_solid_frac:
            hard_fail(
                f"G-open-under: interior mid-height solid frac {frac:.2f} > "
                f"{args.open_under_solid_frac:.2f} for equipment-open-frame — "
                f"empty under seating (no waffle/pin forest)"
            )
        elif frac > args.open_under_solid_frac * 0.75:
            soft_warn(f"G-open-under: interior fill {frac:.2f} approaching limit")

    # Component heuristic: unique vertex count vs triangles (warn only)
    # Skip heavy weld — use triangle count bands
    if ntri > 500_000:
        soft_warn(f"G-components: very dense mesh ({ntri} tris) — export/simplify if accidental")

    _report(hard, warn, info, args.json_summary)
    return 1 if hard else 0


def _report(hard: List[str], warn: List[str], info: List[str], as_json: bool) -> None:
    print("=== dfm_gate ===")
    for line in info:
        print(f"  INFO  {line}")
    for line in warn:
        print(f"  WARN  {line}")
    for line in hard:
        print(f"  HARD  {line}")
    print(f"=== summary: HARD={len(hard)} WARN={len(warn)} ===")
    if hard:
        print("RESULT: FAIL")
    else:
        print("RESULT: PASS")


if __name__ == "__main__":
    sys.exit(main())