#!/usr/bin/env python3
"""Zip a gated PRINT_SPEC project. Calls validate_project.py; does not reimplement it."""
from __future__ import annotations

import argparse
import hashlib
import subprocess
import sys
import zipfile
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parent
VALIDATE = (
    SCRIPTS.parent.parent / "3d-print-validate" / "scripts" / "validate_project.py"
)
BRIEF = SCRIPTS.parent.parent / "3d-print-design-brief" / "scripts"
sys.path.insert(0, str(BRIEF))

from print_spec import load_spec  # noqa: E402

STILL_SUFFIXES = {".png", ".jpg", ".jpeg", ".webp"}


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def print_notes(spec) -> str:
    lines = [
        "# Print notes",
        "",
        "Generated from docs/PRINT_SPEC.yaml only.",
        "",
        f"- orientation: {spec.orientation}",
        f"- bed_face: {spec.bed_face}",
        f"- supports: {spec.supports}",
        f"- material: {spec.material}",
        f"- nozzle_mm: {spec.nozzle_mm}",
        f"- layer_height_mm: {spec.layer_height_mm}",
        "",
    ]
    return "\n".join(lines)


def collect_members(project: Path, spec) -> list[tuple[str, Path]]:
    members: list[tuple[str, Path]] = []
    seen: set[str] = set()

    def add(rel: str, path: Path | None = None) -> None:
        key = Path(rel).as_posix()
        if key in seen:
            return
        target = path if path is not None else project / rel
        if not target.is_file():
            return
        seen.add(key)
        members.append((key, target))

    add("docs/PRINT_SPEC.yaml")
    add("docs/PRINT_NOTES.md")
    for rel in spec.source_files:
        add(rel)
    for body in spec.stl_files:
        add(body.path)
    step = project / "step"
    if step.is_dir():
        for path in sorted(step.rglob("*")):
            if path.is_file():
                add(path.relative_to(project).as_posix(), path)
    renders = project / "renders"
    if renders.is_dir():
        for path in sorted(renders.rglob("*")):
            if path.is_file() and path.suffix.lower() in STILL_SUFFIXES:
                add(path.relative_to(project).as_posix(), path)
    return members


def validate_project(project: Path) -> int:
    result = subprocess.run(
        [sys.executable, str(VALIDATE), str(project)],
        text=True,
        capture_output=True,
        check=False,
    )
    if result.stdout:
        sys.stdout.write(result.stdout)
        if not result.stdout.endswith("\n"):
            sys.stdout.write("\n")
    if result.stderr:
        sys.stderr.write(result.stderr)
    return result.returncode


def pack(project: Path, zip_path: Path | None = None) -> Path:
    spec, errors = load_spec(project / "docs" / "PRINT_SPEC.yaml", project=project)
    if spec is None or errors:
        raise SystemExit("HARD: cannot load PRINT_SPEC.yaml")
    notes_path = project / "docs" / "PRINT_NOTES.md"
    notes_path.parent.mkdir(parents=True, exist_ok=True)
    notes_path.write_text(print_notes(spec), encoding="utf-8")

    members = collect_members(project, spec)
    payload: list[tuple[str, bytes]] = []
    for rel, path in members:
        payload.append((rel, path.read_bytes()))

    manifest_lines = [
        f"{sha256_bytes(data)}  {rel}" for rel, data in payload
    ]
    manifest = "\n".join(manifest_lines) + "\n"
    payload.append(("MANIFEST.sha256", manifest.encode("utf-8")))

    if zip_path is None:
        zip_path = project / "pack" / f"{spec.part_name}.zip"
    zip_path.parent.mkdir(parents=True, exist_ok=True)
    if zip_path.exists():
        zip_path.unlink()
    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        for rel, data in payload:
            if Path(rel).is_absolute() or ".." in Path(rel).parts:
                raise SystemExit(f"HARD: refused non-relative zip member {rel}")
            zf.writestr(rel, data)
    return zip_path


def main() -> int:
    parser = argparse.ArgumentParser(description="Zip a gated FDM project")
    parser.add_argument("project", type=Path)
    parser.add_argument("--out", type=Path, default=None)
    args = parser.parse_args()
    project = args.project.resolve()
    if not (project / "docs" / "PRINT_SPEC.yaml").is_file():
        print("HARD: missing docs/PRINT_SPEC.yaml")
        return 1
    if validate_project(project) != 0:
        print("HARD: validate_project.py failed; refusing to pack")
        return 1
    zip_path = pack(project, args.out.resolve() if args.out else None)
    print(f"PACK: {zip_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
