#!/usr/bin/env python3
"""Dump mill STEP inside FreeCADCmd, pack the CAD inspector, optionally serve."""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from html import escape
from pathlib import Path

from cad_pack import CadPackError, load_dump, study_from_dump

SKILL_DIR = Path(__file__).resolve().parents[1]
DUMP_SCRIPT = Path(__file__).resolve().parent / "dump_cad_scene.py"
TEMPLATE = SKILL_DIR / "viewer" / "viewer.template.html"
BUNDLE = SKILL_DIR / "viewer" / "viewer.bundle.js"


def spec_step_rels(text: str) -> list[str]:
    """Read reverse.step_files, including `- path: exports/part.step` mappings."""
    rels: list[str] = []
    lines = text.splitlines()
    i = 0
    while i < len(lines):
        if lines[i].strip().startswith("step_files:"):
            base = len(lines[i]) - len(lines[i].lstrip())
            i += 1
            while i < len(lines):
                raw = lines[i]
                stripped = raw.strip()
                if stripped and not stripped.startswith("#"):
                    indent = len(raw) - len(raw.lstrip())
                    if indent <= base:
                        break
                rest = ""
                if stripped.startswith("- "):
                    rest = stripped[2:].strip().strip("'\"")
                    if rest.lower().startswith("path:"):
                        rest = rest.split(":", 1)[1].strip().strip("'\"")
                elif stripped.lower().startswith("path:"):
                    rest = stripped.split(":", 1)[1].strip().strip("'\"")
                if rest.lower().endswith((".step", ".stp")) and ".." not in Path(rest).parts:
                    rels.append(rest)
                i += 1
            continue
        i += 1
    return rels


def find_steps(project: Path, explicit: Path | None) -> list[Path]:
    if explicit:
        p = explicit if explicit.is_absolute() else project / explicit
        if not p.is_file():
            raise CadPackError(f"STEP not found: {p}")
        return [p]
    found: list[Path] = []
    for folder in (project / "step", project / "cad"):
        if folder.is_dir():
            found.extend(sorted(folder.glob("*.step")))
            found.extend(sorted(folder.glob("*.stp")))
    spec = project / "docs" / "PRINT_SPEC.yaml"
    if spec.is_file():
        for rel in spec_step_rels(spec.read_text()):
            cand = project / rel
            if cand.is_file():
                found.append(cand)
    # unique preserve order
    out, seen = [], set()
    for p in found:
        key = p.resolve()
        if key not in seen:
            seen.add(key)
            out.append(p)
    if not out:
        stls = list(project.rglob("*.stl"))
        extra = " STL exists — that is a print mesh, not a CAD render." if stls else ""
        raise CadPackError(
            "No STEP/STP in the project. CAD inspector refuses mesh-only." + extra
        )
    return out


def vibecad_cmd() -> Path:
    env = os.environ.get("FREECAD_CMD") or os.environ.get("VIBECAD_CMD")
    if not env:
        raise CadPackError("Set FREECAD_CMD to a FreeCADCmd binary. This pack does not ship one.")
    path = Path(env)
    if not path.is_file():
        raise CadPackError(f"FreeCADCmd missing: {path}")
    return path


def dump_step(step: Path, out_json: Path, cmd: Path) -> dict:
    env = os.environ.copy()
    env["QT_QPA_PLATFORM"] = "offscreen"
    env["CAD_RENDER_STEP"] = str(step.resolve())
    env["CAD_RENDER_OUT"] = str(out_json.resolve())
    out_json.parent.mkdir(parents=True, exist_ok=True)
    proc = subprocess.run(
        [str(cmd), "-c", str(DUMP_SCRIPT)],
        env=env,
        capture_output=True,
        text=True,
        timeout=180,
    )
    if proc.returncode != 0 or not out_json.is_file():
        raise CadPackError(
            "FreeCADCmd dump failed:\n"
            + (proc.stderr or "")
            + (proc.stdout or "")
        )
    return load_dump(out_json)


def merge_dumps(dumps: list[dict], title: str) -> dict:
    parts = []
    step_names = []
    for dump in dumps:
        parts.extend(dump["parts"])
        step_names.append(dump.get("step") or "")
    return {
        "source": "occ-step",
        "step": "+".join(n for n in step_names if n),
        "deflection_mm": dumps[0].get("deflection_mm"),
        "parts": parts,
        "issues": [],
        "title": title,
    }


def build_html(study: dict, dest: Path) -> Path:
    if not TEMPLATE.is_file() or not BUNDLE.is_file():
        raise CadPackError(f"viewer template/bundle missing under {SKILL_DIR / 'viewer'}")
    payload = json.dumps(study, separators=(",", ":")).replace("<", "\\u003c")
    runtime = BUNDLE.read_text().replace("</script", "<\\/script")
    html = (
        TEMPLATE.read_text()
        .replace("/* STUDY_DATA */", payload)
        .replace("/* VIEWER_RUNTIME */", runtime)
        .replace("<!-- TITLE -->", escape(study.get("title") or "CAD inspector", quote=True))
        .replace("<!-- BRAND -->", escape(study.get("brand") or "RAGE INDUSTRIES / CAD INSPECTOR", quote=True))
    )
    dest.mkdir(parents=True, exist_ok=True)
    out = dest / "viewer.html"
    out.write_text(html)
    (dest / "study.json").write_text(json.dumps({"title": study.get("title"), "step": study.get("step"), "solids": len(study["concepts"][0]["items"])}, indent=2) + "\n")
    return out


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project", type=Path)
    parser.add_argument("--step", type=Path)
    parser.add_argument("--scene", type=Path, help="Skip FreeCADCmd; use an existing OCC dump JSON")
    parser.add_argument("--out-dir", type=Path)
    parser.add_argument("--title")
    parser.add_argument("--catalog", type=Path, help="Also register this study in a multi-model catalog root")
    parser.add_argument("--model-id", help="Catalog id (default: project or step stem)")
    parser.add_argument("--serve", action="store_true")
    parser.add_argument("--port", type=int, default=8107)
    parser.add_argument("--bind", default="127.0.0.1")
    args = parser.parse_args(argv)
    if args.bind not in {"127.0.0.1", "localhost", "::1"}:
        print("HARD: bind must be loopback", file=sys.stderr)
        return 2
    try:
        if args.scene:
            dump = load_dump(args.scene)
            title = args.title or dump.get("step") or "CAD inspector"
            project = args.project or args.scene.parent
        else:
            if not args.project:
                parser.error("--project is required unless --scene is set")
            project = args.project.resolve()
            steps = find_steps(project, args.step)
            cmd = vibecad_cmd()
            dumps = []
            raw_dir = project / "renders" / "cad-scene"
            for step in steps:
                dumps.append(dump_step(step, raw_dir / (step.stem + ".scene.json"), cmd))
            dump = merge_dumps(dumps, args.title or project.name)
            title = args.title or project.name
        study = study_from_dump(dump, title=title)
        out_dir = (args.out_dir or (project / "renders" / "cad-inspector")).resolve()
        html = build_html(study, out_dir)
        print(f"CAD inspector: {html} ({html.stat().st_size} bytes)", flush=True)
        print(f"solids={len(study['concepts'][0]['items'])} step={study.get('step')}", flush=True)
        if args.catalog:
            from cad_catalog import build_shell, register_study

            model_id = args.model_id or (project.name if project else Path(study.get("step") or "part").stem)
            model_id = "".join(ch if ch.isalnum() else "-" for ch in model_id.lower()).strip("-")[:64]
            register_study(args.catalog, study, model_id, name=title)
            shell = build_shell(args.catalog)
            print(f"catalog: {args.catalog / 'catalog.json'} shell={shell}", flush=True)
        if args.serve:
            from serve_cad_viewer import make_server

            server = make_server(out_dir, args.port, args.bind)
            print(f"http://{args.bind}:{args.port}/?view=solid", flush=True)
            try:
                server.serve_forever()
            except KeyboardInterrupt:
                pass
            finally:
                server.server_close()
        return 0
    except CadPackError as exc:
        print(f"HARD: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
