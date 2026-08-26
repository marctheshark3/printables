#!/usr/bin/env python3
"""Mesh-only manufacturing checks. Policy lives in PRINT_SPEC.yaml."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import List, Tuple

from dfm import (
    OPEN_FRAME,
    open_under_fill_frac,
    overhang_fraction,
    print_up,
    tessellation_thin_frac,
)
from overlap import count_overlapping_shell_pairs
from stl_io import bbox_and_volume, load_binary_stl
from topology import topology_metrics


def audit_mesh(
    stl: Path,
    *,
    expected_shells: int,
    build: Tuple[float, float, float],
    product_class: str = "",
    orientation: str = "Z-up",
    up_axis: str = "Z",
    min_feature_mm: float = 1.6,
    max_overhang_deg: float = 45.0,
    weld_tolerance_mm: float = 1e-5,
    skip_overhang: bool = False,
    skip_open_under: bool = False,
    overhang_fail_area_frac: float = 0.28,
    bed_support_mm: float = 1.6,
    thin_edge_mm: float = 0.5,
    thin_fail_frac: float = 0.35,
    open_under_solid_frac: float = 0.22,
) -> Tuple[List[str], List[str], List[str]]:
    hard: List[str] = []
    warn: List[str] = []
    info: List[str] = []
    klass = (product_class or "").lower()
    info.append(
        f"mode product_class={klass or '(none)'} orientation={orientation} "
        f"expected_components={expected_shells}"
    )

    if not stl.is_file():
        return [f"G-stl: missing {stl}"], warn, info

    try:
        normals, tris, ntri = load_binary_stl(stl)
    except Exception as exc:
        return [f"G-stl: parse failed: {exc}"], warn, info

    if ntri < 4:
        hard.append(f"G-stl: too few triangles ({ntri})")

    try:
        topo = topology_metrics(tris, weld_tolerance_mm)
        info.append(
            "topology "
            f"verts={topo['vertices']} edges={topo['edges']} "
            f"boundary={topo['boundary_edges']} nonmanifold={topo['nonmanifold_edges']} "
            f"orientation={topo['orientation_edges']} components={topo['components']}"
        )
        if topo["boundary_edges"]:
            hard.append(f"G-topology: {topo['boundary_edges']} boundary edges; mesh is open")
        if topo["nonmanifold_edges"]:
            hard.append(f"G-topology: {topo['nonmanifold_edges']} non-manifold edges")
        if topo["orientation_edges"]:
            hard.append(f"G-topology: {topo['orientation_edges']} inconsistently oriented edges")
        degenerate_limit = max(2, int(ntri * 0.01))
        if topo["degenerate_faces"] > degenerate_limit:
            hard.append(
                f"G-topology: {topo['degenerate_faces']} degenerate faces "
                f"exceed limit {degenerate_limit}"
            )
        elif topo["degenerate_faces"]:
            warn.append(f"G-topology: {topo['degenerate_faces']} degenerate faces")
        if topo["duplicate_faces"]:
            hard.append(f"G-topology: {topo['duplicate_faces']} duplicate faces")
        if topo["components"] != expected_shells:
            hard.append(
                f"G-components: expected {expected_shells}, found {topo['components']} "
                "edge-connected shells"
            )
        overlapping = count_overlapping_shell_pairs(
            tris, topo["tri_cid"], int(topo["components"])
        )
        if overlapping:
            hard.append(
                f"G-overlap: {overlapping} shell pair(s) occupy the same space; "
                "overlapping exported solids are forbidden"
            )
    except Exception as exc:
        hard.append(f"G-topology: audit failed: {exc}")

    mn, mx, signed_vol = bbox_and_volume(tris)
    dx, dy, dz = mx[0] - mn[0], mx[1] - mn[1], mx[2] - mn[2]
    cm3 = signed_vol / 1000.0
    info.append(f"mesh tris={ntri} bbox={dx:.2f}x{dy:.2f}x{dz:.2f} mm vol={cm3:.2f} cm³")
    if signed_vol <= 0:
        hard.append(f"G-volume: signed volume {cm3:.4f} cm³ is not positive")

    build_x, build_y, build_z = build
    if dx >= build_x or dy >= build_y or dz >= build_z:
        hard.append(
            f"G-build-volume: {dx:.1f}×{dy:.1f}×{dz:.1f} mm exceeds "
            f"{build_x:.1f}×{build_y:.1f}×{build_z:.1f} mm"
        )

    up = print_up(orientation, up_axis)
    info.append(f"print_up={up}")
    overhang_limit = overhang_fail_area_frac
    if klass in OPEN_FRAME:
        overhang_limit = max(overhang_limit, 0.30)

    if not skip_overhang and tris:
        frac, thr, bed_excl = overhang_fraction(tris, normals, up, max_overhang_deg, bed_support_mm)
        info.append(
            f"overhang unsupported_frac={frac:.3f} thr_n·up<{thr:.3f} "
            f"max_deg={max_overhang_deg} bed_excl_frac={bed_excl:.3f}"
        )
        if frac > overhang_limit:
            hard.append(
                f"G-overhang: {frac*100:.1f}% unsupported face area steeper than {max_overhang_deg}° "
                f"(limit {overhang_limit*100:.0f}%) — reorient or add 45° structure"
            )
        elif frac > overhang_limit * 0.55:
            warn.append(f"G-overhang: {frac*100:.1f}% unsupported area near overhang limit")

    if tris:
        thin_frac, samples = tessellation_thin_frac(tris, ntri, thin_edge_mm)
        info.append(
            f"thin_edges frac={thin_frac:.3f} thr={thin_edge_mm:.2f} mm "
            f"samples={samples} min_feature={min_feature_mm}"
        )
        if samples and thin_frac > thin_fail_frac:
            warn.append(
                f"G-tessellation: {thin_frac*100:.1f}% edges under {thin_edge_mm:.2f} mm; "
                f"short STL chords do not prove a thin wall. Verify CAD/slicer wall ≥ {min_feature_mm} mm"
            )

    if not skip_open_under and klass in OPEN_FRAME and tris and dz > 5.0:
        frac, under_lo, under_hi = open_under_fill_frac(tris, mn, dx, dy, dz)
        info.append(
            f"open_under interior_solid_frac={frac:.3f} "
            f"band_z=[{under_lo:.1f},{under_hi:.1f}]"
        )
        if frac > open_under_solid_frac:
            hard.append(
                f"G-open-under: interior mid-height solid frac {frac:.2f} > "
                f"{open_under_solid_frac:.2f} for equipment-open-frame — "
                f"empty under seating (no waffle/pin forest)"
            )
        elif frac > open_under_solid_frac * 0.75:
            warn.append(f"G-open-under: interior fill {frac:.2f} approaching limit")

    if ntri > 500_000:
        warn.append(f"G-components: very dense mesh ({ntri} tris) — export/simplify if accidental")
    return hard, warn, info


def report(hard: List[str], warn: List[str], info: List[str]) -> None:
    print("=== validate_stl ===")
    for line in info:
        print(f"  INFO  {line}")
    for line in warn:
        print(f"  WARN  {line}")
    for line in hard:
        print(f"  HARD  {line}")
    print(f"=== summary: HARD={len(hard)} WARN={len(warn)} ===")
    print("RESULT: FAIL" if hard else "RESULT: PASS")


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Mesh manufacturing checks (no PRINT_SPEC policy)")
    p.add_argument("--project", type=Path, default=None)
    p.add_argument("--stl", type=Path, required=True)
    p.add_argument("--product-class", default="")
    p.add_argument("--print-orientation", default="Z-up")
    p.add_argument("--print-up-axis", default="Z", choices=["X", "Y", "Z", "x", "y", "z"])
    p.add_argument("--min-feature-mm", type=float, default=1.6)
    p.add_argument("--overhang-max-deg", type=float, default=45.0)
    p.add_argument("--overhang-fail-area-frac", type=float, default=0.28)
    p.add_argument("--bed-support-mm", type=float, default=1.6)
    p.add_argument("--thin-edge-mm", type=float, default=0.5)
    p.add_argument("--thin-fail-frac", type=float, default=0.35)
    p.add_argument("--open-under-solid-frac", type=float, default=0.22)
    p.add_argument("--expected-components", type=int, default=1)
    p.add_argument("--weld-tolerance-mm", type=float, default=1e-5)
    p.add_argument("--build-x-mm", type=float, required=True)
    p.add_argument("--build-y-mm", type=float, required=True)
    p.add_argument("--build-z-mm", type=float, required=True)
    p.add_argument("--skip-overhang", action="store_true")
    p.add_argument("--skip-open-under", action="store_true")
    return p.parse_args()


def main() -> int:
    args = parse_args()
    project = args.project.resolve() if args.project else None
    stl = args.stl.expanduser()
    if project and not stl.is_absolute():
        stl = (project / stl).resolve()
    else:
        stl = stl.resolve()
    hard, warn, info = audit_mesh(
        stl,
        expected_shells=args.expected_components,
        build=(args.build_x_mm, args.build_y_mm, args.build_z_mm),
        product_class=args.product_class,
        orientation=args.print_orientation,
        up_axis=args.print_up_axis,
        min_feature_mm=args.min_feature_mm,
        max_overhang_deg=args.overhang_max_deg,
        weld_tolerance_mm=args.weld_tolerance_mm,
        skip_overhang=args.skip_overhang,
        skip_open_under=args.skip_open_under,
        overhang_fail_area_frac=args.overhang_fail_area_frac,
        bed_support_mm=args.bed_support_mm,
        thin_edge_mm=args.thin_edge_mm,
        thin_fail_frac=args.thin_fail_frac,
        open_under_solid_frac=args.open_under_solid_frac,
    )
    report(hard, warn, info)
    return 1 if hard else 0


if __name__ == "__main__":
    sys.exit(main())
