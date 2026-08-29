"""Write analytic STEP + binary STL. Refuse triangle-wrapped STEP. No host OCC import."""
from __future__ import annotations

import os
import re
import shutil
import subprocess
from pathlib import Path
from typing import Any

from stl_write import write_binary_stl
from tessellate_solid import tessellate_ir

FACE_RE = re.compile(r"\bADVANCED_FACE\s*\(", re.IGNORECASE)
SOLID_RE = re.compile(r"\bMANIFOLD_SOLID_BREP\s*\(", re.IGNORECASE)
LATEST_RE = re.compile(r":latest(?:$|@|/)")

# Documented CI pin (digest, not :latest). Local cadquery/cadquery:latest is CQ 2.1 / Py 3.8.
DEFAULT_CADQUERY_DIGEST = (
    "ghcr.io/cadquery/cadquery-docker@sha256:"
    "779a5be732d838eb5ed41c2f44a76f3e64fd83b91471241914d762cee3c65be8"
)


def count_step_faces(text: str) -> int:
    return len(FACE_RE.findall(text))


def count_step_solids(text: str) -> int:
    return len(SOLID_RE.findall(text))


def is_triangle_wrapped(face_count: int, input_triangles: int) -> bool:
    if input_triangles <= 0:
        return False
    return face_count >= 0.9 * float(input_triangles)


def inspect_step_file(path: Path) -> tuple[int, int]:
    text = path.read_text(encoding="utf-8", errors="replace")
    return count_step_faces(text), count_step_solids(text)


def refuse_triangle_wrap(
    step_path: Path,
    input_triangles: int,
    dest_dir: Path | None = None,
) -> tuple[bool, str]:
    """Return (refused, message). Must not copy a wrapped STEP into dest_dir."""
    faces, _solids = inspect_step_file(step_path)
    if is_triangle_wrapped(faces, input_triangles):
        return True, (
            f"HARD: triangle-wrapped STEP ({faces} faces vs {input_triangles} input triangles)"
        )
    return False, f"faces={faces} triangles={input_triangles}"


def kernel_is_qemu(cmd: str) -> bool:
    return "qemu" in cmd.lower()


def image_is_latest(image: str) -> bool:
    return bool(LATEST_RE.search(image)) or image.strip().endswith(":latest")


def detect_kernel(requested: str = "auto") -> tuple[str | None, str]:
    """Order: vibecad / VIBECAD_CMD, cadquery / PREVERSE_STEP_IMAGE, PREVERSE_PYTHON."""
    req = (requested or "auto").lower()
    vibecad = os.environ.get("VIBECAD_CMD") or ""
    image = os.environ.get("PREVERSE_STEP_IMAGE") or ""
    py = os.environ.get("PREVERSE_PYTHON") or ""

    if req == "vibecad":
        if not vibecad:
            return None, "missing VIBECAD_CMD"
        if kernel_is_qemu(vibecad):
            return None, "ARM qemu-x86_64 AppImage is unsupported"
        return "vibecad", vibecad
    if req == "cadquery":
        if not image:
            return None, "missing PREVERSE_STEP_IMAGE"
        if image_is_latest(image):
            return None, "PREVERSE_STEP_IMAGE must be a digest pin, not :latest"
        return "cadquery", image
    if req not in {"auto", "cadquery", "vibecad"}:
        return None, f"unknown kernel {requested!r}"

    # auto
    if vibecad:
        if kernel_is_qemu(vibecad):
            return None, "ARM qemu-x86_64 AppImage is unsupported"
        return "vibecad", vibecad
    if image:
        if image_is_latest(image):
            return None, "PREVERSE_STEP_IMAGE must be a digest pin, not :latest"
        return "cadquery", image
    if py:
        return "python", py
    return None, "no STEP kernel (set VIBECAD_CMD, PREVERSE_STEP_IMAGE, or PREVERSE_PYTHON)"


def write_ir_stl(project: Path, ir: dict[str, Any]) -> Path:
    body = ir.get("body") or "body"
    path = project / "stl" / f"{body}.stl"
    tris = tessellate_ir(ir)
    write_binary_stl(path, tris, name=b"preverse")
    return path


def export_with_kernel(
    project: Path,
    ir: dict[str, Any],
    *,
    kernel: str,
    handle: str,
    source: Path,
) -> int:
    body = ir.get("body") or "body"
    step_dest = project / "step" / f"{body}.step"
    step_dest.parent.mkdir(parents=True, exist_ok=True)
    env = os.environ.copy()
    env.setdefault("PRINTABLES_STL", str(project / "stl" / f"{body}.stl"))
    env.setdefault("PRINTABLES_STEP", str(step_dest))
    if kernel == "vibecad":
        result = subprocess.run(
            [handle, str(source)], cwd=str(project), check=False, env=env
        )
        return int(result.returncode)
    if kernel == "cadquery":
        cmd = [
            "docker",
            "run",
            "--rm",
            "-v",
            f"{project.resolve()}:/work",
            "-w",
            "/work",
            handle,
            "python",
            f"/work/src/{body}.py",
        ]
        result = subprocess.run(cmd, check=False, env=env)
        return int(result.returncode)
    if kernel == "python":
        result = subprocess.run(
            [handle, str(source)], cwd=str(project), check=False, env=env
        )
        return int(result.returncode)
    return 2


def gate_exported_step(project: Path, ir: dict[str, Any]) -> tuple[int, str]:
    body = ir.get("body") or "body"
    step_dest = project / "step" / f"{body}.step"
    if not step_dest.is_file():
        return 2, "HARD: kernel did not write STEP"
    ntri = int(ir.get("input_triangles") or 0)
    refused, msg = refuse_triangle_wrap(step_dest, ntri)
    if refused:
        step_dest.unlink(missing_ok=True)
        return 1, msg
    faces, solids = inspect_step_file(step_dest)
    expected = int(ir.get("expected_shells") or 1)
    if solids and solids != expected:
        step_dest.unlink(missing_ok=True)
        return 1, f"HARD: STEP solid count {solids} != expected_shells {expected}"
    if ir.get("class") == "parametric" and int((ir.get("regions") or {}).get("fallback") or 0) > 0:
        step_dest.unlink(missing_ok=True)
        return 1, "HARD: parametric class with fallback > 0"
    return 0, f"STEP ok faces={faces} solids={solids}"
