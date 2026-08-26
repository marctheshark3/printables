#!/usr/bin/env python3
"""pblend — headless Blender printables CLI (host Python; spawns blender)."""
from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys
import zipfile
from pathlib import Path
from typing import Iterable, List, Optional, Sequence

VERSION = "0.2.0"

# skill root = parent of scripts/
SCRIPT_DIR = Path(__file__).resolve().parent
SKILL_ROOT = SCRIPT_DIR.parent
BPY_LIB = SCRIPT_DIR / "bpy_lib"
TEMPLATES = SCRIPT_DIR / "templates"


def skill_root() -> Path:
    return SKILL_ROOT


def find_blender(explicit: Optional[str] = None) -> Optional[str]:
    candidates: List[str] = []
    if explicit:
        candidates.append(explicit)
    env = os.environ.get("BLENDER")
    if env:
        candidates.append(env)
    which = shutil.which("blender")
    if which:
        candidates.append(which)
    candidates.extend(
        [
            "/usr/bin/blender",
            str(Path.home() / "blender" / "blender"),
            "/snap/bin/blender",
        ]
    )
    seen = set()
    for c in candidates:
        if not c or c in seen:
            continue
        seen.add(c)
        p = Path(c)
        if p.is_file() and os.access(p, os.X_OK):
            return str(p)
        # which already absolute
        if shutil.which(c):
            return shutil.which(c)
    return None


def find_project_validator() -> Optional[Path]:
    env = os.environ.get("PRINT_VALIDATOR")
    if env and Path(env).is_file():
        return Path(env)
    legacy = os.environ.get("DFM_GATE")
    if legacy and Path(legacy).is_file():
        print("WARN: DFM_GATE is deprecated; set PRINT_VALIDATOR instead")
        return Path(legacy)
    pack_local = SKILL_ROOT.parent / "3d-print-validate" / "scripts" / "validate_project.py"
    if pack_local.is_file():
        return pack_local
    profiles = Path.home() / ".hermes" / "profiles"
    if profiles.is_dir():
        matches = sorted(
            profiles.glob("*/skills/creative/3d-print-validate/scripts/validate_project.py")
        )
        for candidate in matches:
            if candidate.is_file():
                return candidate
    return None


def run_cmd(cmd: Sequence[str], *, cwd: Optional[Path] = None, env: Optional[dict] = None) -> int:
    print("+", " ".join(cmd))
    r = subprocess.run(list(cmd), cwd=str(cwd) if cwd else None, env=env)
    return int(r.returncode)


def cmd_version(_: argparse.Namespace) -> int:
    print(f"pblend {VERSION}")
    print(f"skill_root={SKILL_ROOT}")
    return 0


def cmd_doctor(args: argparse.Namespace) -> int:
    print(f"pblend {VERSION}")
    print(f"skill_root={SKILL_ROOT}")
    print(f"bpy_lib={BPY_LIB} exists={BPY_LIB.is_dir()}")
    blender = find_blender(args.blender)
    if not blender:
        print("ERROR: blender not found. Install or export BLENDER=/path/to/blender")
        return 1
    print(f"blender={blender}")
    # version
    vr = subprocess.run(
        [blender, "--version"], capture_output=True, text=True, timeout=60
    )
    line = (vr.stdout or vr.stderr or "").splitlines()
    print(f"blender_version_line={line[0] if line else 'unknown'}")

    py_expr = (
        "import bpy,sys;\n"
        "print('bpy_ok', bpy.app.version_string);\n"
        "print('py', sys.version.split()[0]);\n"
        "import numpy; print('numpy', numpy.__version__);\n"
        "try:\n"
        " import scipy; print('scipy', scipy.__version__)\n"
        "except Exception as e:\n"
        " print('scipy', 'MISSING', e)\n"
    )
    pr = subprocess.run(
        [blender, "-b", "--python-expr", py_expr],
        capture_output=True,
        text=True,
        timeout=120,
    )
    out = (pr.stdout or "") + (pr.stderr or "")
    for key in ("bpy_ok", "py ", "numpy", "scipy"):
        for ln in out.splitlines():
            if key in ln:
                print(ln.strip())
                break
    if pr.returncode != 0:
        print("ERROR: blender python-expr failed")
        print(out[-2000:])
        return 1

    validator = find_project_validator()
    if validator:
        print(f"project_validator={validator}")
    else:
        print("WARN: validate_project.py not found; install 3d-print-validate")

    print("craft: cleanup_fdm default=light (never voxel+fatten mechanical shells)")
    print("craft: preview defaults to separate STL stills; vision-check before ship")
    print("craft: OpenSCAD = dimensional default; Blender = organic/lattice only")
    mcp_skill = Path.home() / ".hermes/hermes-agent/optional-skills/creative/blender-mcp/SKILL.md"
    print(f"optional_mcp_skill={mcp_skill} exists={mcp_skill.is_file()}")
    print("optional_mcp: hermes mcp install blender + GUI/xvfb addon (explore only; ship via pblend)")

    print("doctor: OK")
    return 0


def _write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _render_template(name: str, mapping: dict) -> str:
    src = TEMPLATES / name
    text = src.read_text(encoding="utf-8")
    for k, v in mapping.items():
        text = text.replace("{{" + k + "}}", str(v))
    return text


def cmd_new(args: argparse.Namespace) -> int:
    name = args.name.strip().replace(" ", "-")
    if not name:
        print("ERROR: empty name")
        return 1
    root = Path(args.root).expanduser().resolve()
    project = root / name
    if project.exists() and any(project.iterdir()) and not args.force:
        print(f"ERROR: {project} exists (use --force to overwrite templates carefully)")
        return 1

    product_class = args.product_class
    mapping = {
        "NAME": name,
        "PRODUCT_CLASS": product_class,
        "VERSION": "v0.1.0",
    }

    (project / "src").mkdir(parents=True, exist_ok=True)
    (project / "stl").mkdir(parents=True, exist_ok=True)
    (project / "renders").mkdir(parents=True, exist_ok=True)
    (project / "docs").mkdir(parents=True, exist_ok=True)
    (project / "scripts").mkdir(parents=True, exist_ok=True)

    _write_text(project / "docs" / "DESIGN.md", _render_template("DESIGN.md.tmpl", mapping))
    _write_text(project / "docs" / "PRINT_SPEC.yaml", _render_template("PRINT_SPEC.yaml.tmpl", mapping))
    _write_text(project / "src" / "build.py", _render_template("build_part.py.tmpl", mapping))
    _write_text(project / "README.md", _render_template("README.md.tmpl", mapping))
    _write_text(project / "scripts" / "export.sh", _render_template("export.sh.tmpl", mapping))
    os.chmod(project / "scripts" / "export.sh", 0o755)

    # pointer for agents
    _write_text(
        project / "scripts" / "pblend.path",
        str(SCRIPT_DIR / "pblend") + "\n",
    )

    print(f"Created {project}")
    print(f"  docs/PRINT_SPEC.yaml  backend=blender class={product_class}")
    print("  docs/DESIGN.md  supplemental narrative")
    print(f"  src/build.py")
    print(f"Next: pblend run --project {project}")
    return 0


def _project_from_args(args: argparse.Namespace) -> Path:
    if getattr(args, "project", None):
        return Path(args.project).expanduser().resolve()
    return Path.cwd().resolve()


def _blender_env(project: Path) -> dict:
    env = os.environ.copy()
    env["PBLEND_PROJECT"] = str(project)
    env["PBLEND_LIB"] = str(SCRIPT_DIR)  # parent of bpy_lib package dir
    env["PBLEND_SKILL"] = str(SKILL_ROOT)
    # Also put scripts on PYTHONPATH for non-blender helpers if needed
    pp = env.get("PYTHONPATH", "")
    env["PYTHONPATH"] = str(SCRIPT_DIR) + (os.pathsep + pp if pp else "")
    return env


def cmd_run(args: argparse.Namespace) -> int:
    project = _project_from_args(args)
    script = Path(args.script) if args.script else project / "src" / "build.py"
    if not script.is_file():
        # gold-style alternate
        alt = project / "src" / "build_case.py"
        if alt.is_file():
            script = alt
        else:
            print(f"ERROR: no build script at {script}")
            return 1

    blender = find_blender(args.blender)
    if not blender:
        print("ERROR: blender not found")
        return 1

    # forward args after -- already in args.forward
    forward: List[str] = list(args.forward or [])
    # convenience: --which / --out if provided as pblend flags
    if args.which and "--which" not in forward:
        forward = ["--which", args.which, *forward]
    if args.out and "--out" not in forward:
        forward = ["--out", str(Path(args.out).expanduser().resolve()), *forward]
    if args.blend and "--blend" not in forward:
        forward = ["--blend", *forward]

    cmd = [blender, "-b", "-P", str(script)]
    if forward:
        cmd.append("--")
        cmd.extend(forward)

    env = _blender_env(project)
    rc = run_cmd(cmd, cwd=project, env=env)
    return rc


def cmd_export(args: argparse.Namespace) -> int:
    # alias to run
    return cmd_run(args)


def _iter_printable_stls(project: Path, stls: Optional[Sequence[str]]) -> List[Path]:
    if stls:
        return [Path(s).expanduser().resolve() for s in stls]
    stl_dir = project / "stl"
    if not stl_dir.is_dir():
        return []
    out = []
    for p in sorted(stl_dir.glob("*.stl")):
        name = p.name.lower()
        if "assembly" in name:
            continue
        out.append(p)
    return out


def cmd_gate(args: argparse.Namespace) -> int:
    project = _project_from_args(args)
    validator = find_project_validator()
    if not validator:
        print("ERROR: validate_project.py not found; install 3d-print-validate")
        return 1
    return run_cmd([sys.executable, str(validator), str(project)])


def cmd_preview(args: argparse.Namespace) -> int:
    """Render stills via a tiny blender script, or fall back to note."""
    project = _project_from_args(args)
    blender = find_blender(args.blender)
    if not blender:
        print("ERROR: blender not found")
        return 1

    # Prefer running project's build with --preview if supported; else use helper script
    helper = SCRIPT_DIR / "bpy_preview_runner.py"
    if not helper.is_file():
        print(f"ERROR: missing {helper}")
        return 1

    env = _blender_env(project)
    cmd = [
        blender,
        "-b",
        "-P",
        str(helper),
        "--",
        "--project",
        str(project),
        "--prefix",
        args.prefix or project.name,
    ]
    if args.objects:
        cmd.extend(["--objects", args.objects])
    return run_cmd(cmd, cwd=project, env=env)


def cmd_pack(args: argparse.Namespace) -> int:
    project = _project_from_args(args)
    ver = args.version or "v0.1.0"
    stl_dir = project / "stl"
    renders = project / "renders"
    out = Path(args.out).expanduser() if args.out else stl_dir / f"{project.name}-{ver}.zip"
    out.parent.mkdir(parents=True, exist_ok=True)

    files: List[Path] = []
    files.extend(_iter_printable_stls(project, None))
    if renders.is_dir():
        files.extend(sorted(renders.glob("*.png")))
    for extra in (project / "docs" / "PRINT_SPEC.yaml", project / "docs" / "DESIGN.md", project / "README.md"):
        if extra.is_file():
            files.append(extra)

    if not any(p.suffix.lower() == ".stl" for p in files):
        print("ERROR: no STLs to pack")
        return 1

    with zipfile.ZipFile(out, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        for f in files:
            zf.write(f, arcname=f.name)
            print(f"  + {f.name}")
    print(f"Wrote {out} ({out.stat().st_size} bytes)")
    return 0


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="pblend",
        description="Headless Blender printables CLI (bpy → STL → DFM gate)",
    )
    p.add_argument("--blender", default=None, help="Path to blender binary")
    sub = p.add_subparsers(dest="cmd", required=True)

    s = sub.add_parser("version", help="Print pblend version")
    s.set_defaults(func=cmd_version)

    s = sub.add_parser("doctor", help="Check Blender and project validator")
    s.set_defaults(func=cmd_doctor)

    s = sub.add_parser("new", help="Scaffold a validated FDM project")
    s.add_argument("name")
    s.add_argument(
        "--root",
        default=os.environ.get("PRINT_PROJECTS", str(Path.home() / "print-projects")),
        help="Parent directory for project",
    )
    s.add_argument(
        "--class",
        dest="product_class",
        default="enclosure",
        choices=["bracket", "mount", "stand", "tray", "enclosure", "equipment-open-frame", "wet-fixture", "pip-hinge", "silhouette", "other"],
    )
    s.add_argument("--force", action="store_true")
    s.set_defaults(func=cmd_new)

    def add_project_flags(sp: argparse.ArgumentParser) -> None:
        sp.add_argument("--project", default=None, help="Project root (default: cwd)")

    s = sub.add_parser("run", help="blender -b -P src/build.py")
    add_project_flags(s)
    s.add_argument("--script", default=None, help="Override build script path")
    s.add_argument("--which", default=None, help="Forwarded to build script")
    s.add_argument("--out", default=None, help="Forwarded output dir")
    s.add_argument("--blend", action="store_true", help="Ask build script to save .blend")
    s.add_argument(
        "forward",
        nargs=argparse.REMAINDER,
        help="Args after -- forwarded to build script",
    )
    s.set_defaults(func=cmd_run)

    s = sub.add_parser("export", help="Alias for run")
    add_project_flags(s)
    s.add_argument("--script", default=None)
    s.add_argument("--which", default=None)
    s.add_argument("--out", default=None)
    s.add_argument("--blend", action="store_true")
    s.add_argument("forward", nargs=argparse.REMAINDER)
    s.set_defaults(func=cmd_export)

    s = sub.add_parser("gate", help="Validate PRINT_SPEC.yaml and declared STLs")
    add_project_flags(s)
    s.set_defaults(func=cmd_gate)

    s = sub.add_parser("preview", help="Workbench stills into renders/")
    add_project_flags(s)
    s.add_argument("--prefix", default=None)
    s.add_argument("--objects", default=None, help="Comma object names (default: all meshes)")
    s.set_defaults(func=cmd_preview)

    s = sub.add_parser("pack", help="Zip STLs + renders + DESIGN/README")
    add_project_flags(s)
    s.add_argument("--version", default=None)
    s.add_argument("--out", default=None)
    s.set_defaults(func=cmd_pack)

    return p


def main(argv: Optional[Sequence[str]] = None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    # strip a leading bare -- from remainder weirdness
    parser = build_parser()
    args = parser.parse_args(argv)
    # cleanup forward: argparse REMAINDER may include leading --
    if hasattr(args, "forward") and args.forward:
        fwd = list(args.forward)
        if fwd and fwd[0] == "--":
            fwd = fwd[1:]
        args.forward = fwd
    return int(args.func(args))


if __name__ == "__main__":
    sys.exit(main())
