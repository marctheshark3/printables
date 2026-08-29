"""Binary STL writer. Complements validate stl_io (load only)."""
from __future__ import annotations

import struct
from pathlib import Path
from typing import Iterable, Sequence

from geom import Tri, Vec3, tri_normal


def write_binary_stl(path: Path, tris: Sequence[Tri], name: bytes = b"preverse") -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    header = bytearray(80)
    label = name[:80]
    header[: len(label)] = label
    payload = [bytes(header), struct.pack("<I", len(tris))]
    for a, b, c in tris:
        n = tri_normal(a, b, c)
        payload.append(struct.pack("<12fH", *n, *a, *b, *c, 0))
    path.write_bytes(b"".join(payload))


def write_ascii_stl(path: Path, tris: Iterable[Tri], name: str = "preverse") -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = [f"solid {name}"]
    for a, b, c in tris:
        n = tri_normal(a, b, c)
        lines.append(f"  facet normal {n[0]} {n[1]} {n[2]}")
        lines.append("    outer loop")
        for p in (a, b, c):
            lines.append(f"      vertex {p[0]} {p[1]} {p[2]}")
        lines.append("    endloop")
        lines.append("  endfacet")
    lines.append(f"endsolid {name}")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
