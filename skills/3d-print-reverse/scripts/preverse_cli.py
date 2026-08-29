#!/usr/bin/env python3
"""preverse — rebuild an STL as editable STEP and a gated STL (reconstruction)."""
from __future__ import annotations

import argparse
import os
import subprocess
import sys
from pathlib import Path
from typing import Any, Optional, Sequence

VERSION = "0.1.0"
SCRIPT_DIR = Path(__file__).resolve().parent
SKILL_ROOT = SCRIPT_DIR.parent
PACK_ROOT = SKILL_ROOT.parent.parent

from compare_deviation import compare_meshes, write_report  # noqa: E402
from emit_print_spec import spec_from_ir, write_print_spec  # noqa: E402
from export_step import (  # noqa: E402
    detect_kernel,
    export_with_kernel,
    gate_exported_step,
)
from extract_sketches import apply_sketches  # noqa: E402
from hypothesize_features import hypothesize_features  # noqa: E402
from ir_io import ir_path, load_ir, write_ir  # noqa: E402
from mesh_analyze import analyze_stl  # noqa: E402
from rebuild_cad import write_kernel_source  # noqa: E402
from segment_surfaces import apply_segment, load_aligned_mesh  # noqa: E402
from tessellate_solid import tessellate_ir  # noqa: E402


def find_spec_validator() -> Optional[Path]:
    candidate = PACK_ROOT / "skills" / "3d-print-design-brief" / "scripts" / "validate_print_spec.py"
    if candidate.is_file():
        return candidate
    local = SKILL_ROOT.parent / "3d-print-design-brief" / "scripts" / "validate_print_spec.py"
    return local if local.is_file() else None


def find_project_validator() -> Optional[Path]:
    env = os.environ.get("PRINT_VALIDATOR")
    if env and Path(env).is_file():
        return Path(env)
    candidate = PACK_ROOT / "skills" / "3d-print-validate" / "scripts" / "validate_project.py"
    if candidate.is_file():
        return candidate
    local = SKILL_ROOT.parent / "3d-print-validate" / "scripts" / "validate_project.py"
    return local if local.is_file() else None


def _rel_stl(project: Path, stl: Path) -> str:
    try:
        return str(stl.resolve().relative_to(project.resolve()))
    except ValueError:
        return str(Path("source") / stl.name)


def _resolve_input_stl(project: Path, ir: dict[str, Any], stl: Optional[Path]) -> Path:
    if stl is not None:
        return stl
    rel = ir.get("input_stl")
    if rel:
        cand = project / rel
        if cand.is_file():
            return cand
    source = project / "source"
    if source.is_dir():
        found = sorted(source.glob("*.stl"))
        if found:
            return found[0]
    raise FileNotFoundError("input STL not found")


def _load_or_analyze(args: argparse.Namespace) -> tuple[dict[str, Any], Path, int]:
    project: Path = args.project
    body = args.body
    dest = ir_path(project, body)
    stl = getattr(args, "stl", None)
    cmd = getattr(args, "cmd", None)
    if dest.is_file() and cmd not in {"analyze", "run"}:
        return load_ir(dest), dest, 0
    if stl is None:
        if dest.is_file():
            ir = load_ir(dest)
            return ir, dest, 0
        print("HARD: --stl is required when IR is missing", file=sys.stderr)
        return {}, dest, 2
    if not Path(stl).is_file():
        print(f"HARD: STL not found: {stl}", file=sys.stderr)
        return {}, dest, 2
    ir, code = analyze_stl(
        Path(stl),
        body=body,
        units=getattr(args, "units", "mm"),
        origin=getattr(args, "origin", "center"),
        force=getattr(args, "force", False),
        fit_mm=getattr(args, "fit_mm", 0.05),
        max_deviation_mm=getattr(args, "max_deviation_mm", 0.2),
        snap_mm=getattr(args, "snap_mm", None),
        input_rel=_rel_stl(project, Path(stl)),
    )
    write_ir(dest, ir)
    return ir, dest, code


def cmd_analyze(args: argparse.Namespace) -> int:
    if args.stl is None or not Path(args.stl).is_file():
        print("HARD: --stl is required and must exist", file=sys.stderr)
        return 2
    ir, dest, code = _load_or_analyze(args)
    if not ir:
        return 2
    write_ir(dest, ir)
    print(f"wrote {dest} class={ir.get('class')} triangles={ir.get('input_triangles')}")
    return code


def _ensure_segmented(args: argparse.Namespace, ir: dict[str, Any], dest: Path) -> tuple[dict[str, Any], int]:
    stl = _resolve_input_stl(args.project, ir, getattr(args, "stl", None))
    mesh = load_aligned_mesh(stl, ir, units=getattr(args, "units", "mm"))
    ir = apply_segment(mesh=mesh, ir=ir, dihedral_deg=getattr(args, "dihedral_deg", 15.0))
    write_ir(dest, ir)
    return ir, 0


def cmd_segment(args: argparse.Namespace) -> int:
    ir, dest, code = _load_or_analyze(args)
    if code == 2 and not ir:
        return 2
    if not ir:
        return 2
    ir, _ = _ensure_segmented(args, ir, dest)
    counts = ir.get("regions") or {}
    print(f"segmented planes={counts.get('plane')} cylinders={counts.get('cylinder')} fallback={counts.get('fallback')}")
    return 0 if not ir.get("open_mesh_forced") or args.force else 0


def cmd_sketch(args: argparse.Namespace) -> int:
    ir, dest, code = _load_or_analyze(args)
    if not ir:
        return 2
    if not ir.get("region_list"):
        ir, _ = _ensure_segmented(args, ir, dest)
    stl = _resolve_input_stl(args.project, ir, getattr(args, "stl", None))
    mesh = load_aligned_mesh(stl, ir, units=getattr(args, "units", "mm"))
    if not ir.get("_segment_face_ids"):
        ir, _ = _ensure_segmented(args, ir, dest)
        mesh = load_aligned_mesh(stl, ir, units=getattr(args, "units", "mm"))
    ir = apply_sketches(ir, mesh)
    write_ir(dest, ir)
    print(f"sketches={len(ir.get('sketches') or [])}")
    return 0


def cmd_features(args: argparse.Namespace) -> int:
    ir, dest, code = _load_or_analyze(args)
    if not ir:
        return 2
    if not ir.get("region_list"):
        ir, _ = _ensure_segmented(args, ir, dest)
    if not ir.get("sketches"):
        stl = _resolve_input_stl(args.project, ir, getattr(args, "stl", None))
        mesh = load_aligned_mesh(stl, ir, units=getattr(args, "units", "mm"))
        if not ir.get("_segment_face_ids"):
            ir, _ = _ensure_segmented(args, ir, dest)
            mesh = load_aligned_mesh(stl, ir, units=getattr(args, "units", "mm"))
        ir = apply_sketches(ir, mesh)
    ir = hypothesize_features(ir, organic_ok=getattr(args, "organic_ok", False))
    write_ir(dest, ir)
    print(f"class={ir.get('class')} features={len(ir.get('features') or [])}")
    return 0


def cmd_spec(args: argparse.Namespace) -> int:
    ir, dest, code = _load_or_analyze(args)
    if not ir:
        return 2
    if not ir.get("features"):
        feat_code = cmd_features(args)
        ir = load_ir(dest)
        if feat_code not in (0, 1):
            return feat_code
    kernel = getattr(args, "kernel", "auto")
    detected, _handle = detect_kernel(kernel)
    backend_kernel = detected if detected in {"cadquery", "vibecad"} else "cadquery"
    if kernel == "vibecad":
        backend_kernel = "vibecad"
    spec = spec_from_ir(
        ir,
        kernel=backend_kernel,
        part_name=getattr(args, "part_name", None),
        product_class=getattr(args, "product_class", "bracket"),
    )
    path = write_print_spec(args.project, spec)
    print(f"wrote {path} backend={spec['cad']['backend']}")
    return 0


def cmd_rebuild(args: argparse.Namespace) -> int:
    ir, dest, code = _load_or_analyze(args)
    if not ir:
        return 2
    if not ir.get("features"):
        cmd_features(args)
        ir = load_ir(dest)
    requested = getattr(args, "kernel", "auto")
    detected, handle = detect_kernel(requested)
    emit_as = requested if requested in {"cadquery", "vibecad"} else (detected or "cadquery")
    if emit_as == "python":
        emit_as = "cadquery"
    path = write_kernel_source(args.project, ir, emit_as if emit_as in {"cadquery", "vibecad"} else "cadquery")
    print(f"wrote {path} kernel={emit_as}")
    return 0


def _refuse_delivery(ir: dict[str, Any], force: bool) -> Optional[int]:
    if ir.get("open_mesh_forced") or (force and ir.get("class") == "failed" and ir.get("topology", {}).get("boundary_edges")):
        print("HARD: --force may analyze an open mesh but must not deliver STEP/STL", file=sys.stderr)
        return 1
    if ir.get("class") == "failed":
        print("HARD: class=failed; no STEP/STL claim", file=sys.stderr)
        return 1
    return None


def cmd_export(args: argparse.Namespace) -> int:
    ir, dest, code = _load_or_analyze(args)
    if not ir:
        return 2
    if not ir.get("features"):
        cmd_features(args)
        ir = load_ir(dest)
    blocked = _refuse_delivery(ir, getattr(args, "force", False))
    if blocked is not None:
        return blocked
    requested = getattr(args, "kernel", "auto")
    detected, handle = detect_kernel(requested)
    if detected is None:
        print(f"HARD: {handle}", file=sys.stderr)
        return 2
    emit_as = "vibecad" if detected == "vibecad" else "cadquery"
    source = write_kernel_source(args.project, ir, emit_as)
    rc = export_with_kernel(args.project, ir, kernel=detected, handle=handle, source=source)
    if rc != 0:
        print(f"HARD: kernel export failed exit={rc}", file=sys.stderr)
        return 2 if rc == 2 else 1
    gated, msg = gate_exported_step(args.project, ir)
    print(msg)
    if gated != 0:
        return gated
    body = ir.get("body") or args.body
    kernel_stl = args.project / "stl" / f"{body}.stl"
    if not kernel_stl.is_file():
        print("HARD: kernel did not write STL", file=sys.stderr)
        return 1
    from mesh_common import load_mesh
    from compare_deviation import two_sided_deviation

    kernel_tris = load_mesh(kernel_stl).triangles_xyz()
    ir_tris = tessellate_ir(ir)
    vs_ir = two_sided_deviation(kernel_tris, ir_tris)
    budget = float(ir.get("tolerance", {}).get("max_deviation_mm", 0.2))
    if float(vs_ir["max"]) > budget + 1e-9:
        step = args.project / "step" / f"{body}.step"
        if step.is_file():
            step.unlink()
        print(
            f"HARD: kernel solid != IR (max {vs_ir['max']} mm > {budget} mm); STEP refused",
            file=sys.stderr,
        )
        return 1
    return 0


def cmd_compare(args: argparse.Namespace) -> int:
    ir, dest, code = _load_or_analyze(args)
    if not ir:
        return 2
    if not ir.get("features"):
        cmd_features(args)
        ir = load_ir(dest)
    stl = _resolve_input_stl(args.project, ir, getattr(args, "stl", None))
    rebuilt_path = args.project / "stl" / f"{ir.get('body') or args.body}.stl"
    from mesh_common import load_mesh
    from stl_write import write_binary_stl

    if rebuilt_path.is_file():
        tris = load_mesh(rebuilt_path).triangles_xyz()
    else:
        tris = tessellate_ir(ir)
        write_binary_stl(rebuilt_path, tris, name=b"preverse")
    report = compare_meshes(stl, tris, ir)
    out = args.project / "reports" / f"{ir.get('body') or args.body}.deviation.json"
    write_report(out, report)
    print(f"wrote {out} max={report['max']} pass={report['pass']}")
    if not report["pass"]:
        print("HARD: deviation exceeds max_deviation_mm", file=sys.stderr)
        return 1
    return 0


def cmd_gate(args: argparse.Namespace) -> int:
    project: Path = args.project
    spec = project / "docs" / "PRINT_SPEC.yaml"
    if not spec.is_file():
        rc = cmd_spec(args)
        if rc != 0:
            return rc
    validator = find_spec_validator()
    if validator is None:
        print("HARD: validate_print_spec.py not found", file=sys.stderr)
        return 2
    r1 = subprocess.run([sys.executable, str(validator), str(spec)], check=False)
    if r1.returncode:
        return 1
    ir, dest, code = _load_or_analyze(args)
    if not ir:
        return 2
    if ir.get("class") == "failed":
        print("HARD: class=failed; no STEP/STL claim", file=sys.stderr)
        return 1
    cmp_rc = cmd_compare(args)
    if cmp_rc != 0:
        return cmp_rc
    proj_v = find_project_validator()
    if proj_v is None:
        print("HARD: validate_project.py not found", file=sys.stderr)
        return 2
    r2 = subprocess.run([sys.executable, str(proj_v), str(project)], check=False)
    if r2.returncode:
        return 1
    print("gate: PASS")
    return 0


def cmd_run(args: argparse.Namespace) -> int:
    if args.stl is None:
        print("HARD: preverse run requires --stl", file=sys.stderr)
        return 2
    orig = args.cmd
    try:
        for name, step in (
            ("analyze", cmd_analyze),
            ("segment", cmd_segment),
            ("sketch", cmd_sketch),
            ("features", cmd_features),
            ("spec", cmd_spec),
            ("rebuild", cmd_rebuild),
        ):
            args.cmd = name
            rc = step(args)
            if rc == 2:
                return 2
            if rc == 1 and name == "analyze":
                return 1
        ir = load_ir(ir_path(args.project, args.body))
        blocked = _refuse_delivery(ir, getattr(args, "force", False))
        if blocked is not None:
            return blocked
        args.cmd = "export"
        exp = cmd_export(args)
        if exp == 2:
            return 2
        if exp != 0:
            return exp
        args.cmd = "gate"
        return cmd_gate(args)
    finally:
        args.cmd = orig


def cmd_version(_: argparse.Namespace) -> int:
    print(f"preverse {VERSION}")
    print(f"skill_root={SKILL_ROOT}")
    return 0


def _add_common(p: argparse.ArgumentParser) -> None:
    p.add_argument("--project", type=Path, required=True)
    p.add_argument("--stl", type=Path, default=None)
    p.add_argument("--body", default="body")
    p.add_argument("--units", choices=("mm", "inch"), default="mm")
    p.add_argument("--origin", choices=("center",), default="center")
    p.add_argument("--force", action="store_true")
    p.add_argument("--fit-mm", dest="fit_mm", type=float, default=0.05)
    p.add_argument("--max-deviation-mm", dest="max_deviation_mm", type=float, default=0.2)
    p.add_argument("--snap-mm", dest="snap_mm", type=float, default=None)
    p.add_argument("--dihedral-deg", dest="dihedral_deg", type=float, default=15.0)
    p.add_argument("--kernel", default="auto", choices=("auto", "cadquery", "vibecad"))
    p.add_argument("--organic-ok", dest="organic_ok", action="store_true")
    p.add_argument("--part-name", dest="part_name", default=None)
    p.add_argument("--product-class", dest="product_class", default="bracket")


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="Rebuild an STL as editable STEP and gated STL")
    sub = p.add_subparsers(dest="cmd", required=True)
    for name, func, help_text in (
        ("analyze", cmd_analyze, "Load STL, topology, AABB/PCA align, units"),
        ("segment", cmd_segment, "Dihedral region grow; fit plane/cylinder/cone/sphere"),
        ("sketch", cmd_sketch, "Planar sections; 2D line/arc/circle"),
        ("features", cmd_features, "Hypothesis: extrude/revolve/loft/hole/fillet/chamfer/mirror"),
        ("spec", cmd_spec, "Emit/update docs/PRINT_SPEC.yaml"),
        ("rebuild", cmd_rebuild, "IR → kernel source"),
        ("export", cmd_export, "Write step/*.step and stl/*.stl"),
        ("compare", cmd_compare, "Two-sided sampled deviation vs input STL"),
        ("gate", cmd_gate, "validate_print_spec + validate_project + deviation HARD"),
        ("run", cmd_run, "analyze → … → gate"),
        ("version", cmd_version, "Print version"),
    ):
        s = sub.add_parser(name, help=help_text)
        if name != "version":
            _add_common(s)
        s.set_defaults(func=func)
    return p


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(list(sys.argv[1:] if argv is None else argv))
    try:
        return int(args.func(args))
    except FileNotFoundError as exc:
        print(f"HARD: {exc}", file=sys.stderr)
        return 2
    except ValueError as exc:
        print(f"HARD: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
