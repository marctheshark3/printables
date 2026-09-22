#!/usr/bin/env python3
"""Repository-level naming and routing contract for every published skill."""
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
SKILLS = ROOT / "skills"
EXPECTED = {
    "3d-print-design-brief",
    "3d-print-openscad",
    "3d-print-blender",
    "3d-print-vibecad",
    "3d-print-validate",
    "3d-print-display-enclosure",
    "3d-print-image-silhouette",
    "3d-print-photo-cad",
    "3d-print-shop-fixture",
    "3d-print-robotics",
    "3d-print-sim",
    "3d-print-reverse",
    "3d-print-pack",
    "3d-print-slice",
    "3d-print-cad-render",
}
FORBIDDEN = {
    "printables-part-brief",
    "openscad-printables",
    "printables-dfm-gate",
    "blender-printables",
    "vibecad-printables",
}


def frontmatter(path: Path) -> dict:
    text = path.read_text(encoding="utf-8")
    assert text.startswith("---\n"), f"{path}: frontmatter must start at byte zero"
    _, raw, body = text.split("---", 2)
    assert body.strip(), f"{path}: body is empty"
    data = yaml.safe_load(raw)
    assert isinstance(data, dict), f"{path}: frontmatter is not a mapping"
    return data


def main() -> int:
    found = {path.parent.name for path in SKILLS.glob("*/SKILL.md")}
    assert found == EXPECTED, f"skill set mismatch: expected={sorted(EXPECTED)} found={sorted(found)}"

    for name in sorted(found):
        path = SKILLS / name / "SKILL.md"
        data = frontmatter(path)
        assert data["name"] == name, f"{path}: name must match directory"
        description = data["description"]
        assert isinstance(description, str) and len(description) <= 60
        assert description.endswith("."), f"{path}: description must end with a period"
        assert data.get("author") == "Marc Mailloux, Hermes Agent"
        assert isinstance(data.get("platforms"), list) and data["platforms"]
        related = data.get("metadata", {}).get("hermes", {}).get("related_skills", [])
        assert all(item in EXPECTED for item in related), f"{path}: unresolved related skill"
        text = path.read_text(encoding="utf-8")
        assert not any(old in text for old in FORBIDDEN), f"{path}: deprecated skill name remains"
        print(f"PASS {name}: description={len(description)}")

    bundle = yaml.safe_load((ROOT / "skill-bundles" / "3d-print.yaml").read_text(encoding="utf-8"))
    assert bundle["name"] == "3d-print"
    assert all(item in EXPECTED for item in bundle["skills"])
    assert "3d-print-vibecad" in bundle["skills"]
    assert "3d-print-openscad" in bundle["skills"]
    assert "3d-print-cad-render" not in bundle["skills"]
    assert "3d-print-reverse" not in bundle["skills"]
    assert "3d-print-pack" not in bundle["skills"]
    assert "3d-print-slice" not in bundle["skills"]
    ci = (ROOT / ".github" / "workflows" / "ci.yml").read_text(encoding="utf-8")
    assert "python3 -m pip install PyYAML pytest" in ci
    assert "Bambu Studio" not in ci
    assert "orca" not in ci.lower()
    assert "mqtt" not in ci.lower()
    assert "bambu-mcp" not in ci
    assert not (ROOT / ".gitmodules").exists() or "bambu-mcp" not in (ROOT / ".gitmodules").read_text(encoding="utf-8")
    assert not (SKILLS / "vibecad-printables").exists()
    install = (ROOT / "install.sh").read_text(encoding="utf-8")
    assert "3d-print-vibecad" in install
    assert "3d-print-reverse" in install
    assert "3d-print-pack" in install
    assert "3d-print-slice" in install
    assert "3d-print-cad-render" not in install
    assert "3d-print-photo-cad" in install
    assert "3d-print-photo-cad" not in bundle["skills"]

    vibecad = (SKILLS / "3d-print-vibecad" / "SKILL.md").read_text(encoding="utf-8")
    host = (SKILLS / "3d-print-vibecad" / "references" / "vibecad-host.md").read_text(
        encoding="utf-8"
    )
    combined = vibecad + "\n" + host
    for needle in (
        "3d-print-design-brief",
        "validate_project.py",
        "expected_shells",
        "multiFuse",
        "127.0.0.1:8766",
        "VIBECAD_CMD",
        "Do not enable VibeCAD MCP",
        "passwords",
        "device codes",
        "x86_64",
        "freecadcmd",
        "PRINT_SPEC.yaml",
        "preview is not printable",
        "OpenSCAD is not the dimensional default when VibeCAD resolves",
        "find_vibecad.py",
        "10-X-eng/vibecad/releases",
    ):
        assert needle in combined, f"3d-print-vibecad host contract missing {needle!r}"

    reverse = (SKILLS / "3d-print-reverse" / "SKILL.md").read_text(encoding="utf-8")
    for needle in (
        "preverse",
        "PRINT_SPEC.yaml",
        "validate_project.py",
        "triangle-wrapped",
        "VIBECAD_CMD",
        "PREVERSE_STEP_IMAGE",
        "mesh.to_shape",
        "cadquery",
        "Do not enable VibeCAD MCP",
    ):
        assert needle in reverse, f"3d-print-reverse missing {needle!r}"

    pack = (SKILLS / "3d-print-pack" / "SKILL.md").read_text(encoding="utf-8")
    for needle in ("validate_project.py", "PRINT_NOTES.md", "MANIFEST.sha256"):
        assert needle in pack, f"3d-print-pack missing {needle!r}"

    slice_skill = (SKILLS / "3d-print-slice" / "SKILL.md").read_text(encoding="utf-8")
    for needle in (
        "SKIP: no slicer CLI",
        "bambu-mcp",
        "A validated STL is not permission",
        "process.json",
        "ORCA_SLICER",
    ):
        assert needle in slice_skill, f"3d-print-slice missing {needle!r}"

    render = (SKILLS / "3d-print-cad-render" / "SKILL.md").read_text(encoding="utf-8")
    for needle in (
        "127.0.0.1",
        "viewer.html",
        "Not a trimesh STL preview",
        "does not ship a network proxy",
        "FREECAD_CMD",
    ):
        assert needle in render, f"3d-print-cad-render missing {needle!r}"

    photo = (SKILLS / "3d-print-photo-cad" / "SKILL.md").read_text(encoding="utf-8")
    for needle in (
        "charuco_photo.py",
        "15.0 mm",
        "0.15",
        "photo-derived",
        "XY only",
        "board plane",
        "part_px_are_metric",
        "opencv-python",
    ):
        assert needle in photo, f"3d-print-photo-cad missing {needle!r}"

    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    status = (ROOT / "STATUS.md").read_text(encoding="utf-8")
    contributing = (ROOT / "CONTRIBUTING.md").read_text(encoding="utf-8")
    ci = (ROOT / ".github" / "workflows" / "ci.yml").read_text(encoding="utf-8")
    pytest_paths = (
        "skills/3d-print-cad-render/tests skills/3d-print-image-silhouette/tests "
        "skills/3d-print-photo-cad/tests tests/test_prompt_scenarios.py tests/test_secret_scan.py"
    )
    for label, text in (("README", readme), ("CONTRIBUTING", contributing), ("ci", ci)):
        assert pytest_paths in text, f"{label} test command is missing inspector or silhouette tests"
    for label, text in (("README", readme), ("STATUS", status), ("CONTRIBUTING", contributing)):
        assert "VibeCAD is the dimensional kernel" in text, label
        assert "3d-print-cad-render" in text, label
        assert "upstream FreeCAD" in text, label
        assert "/home/" not in text and "spark-adb4" not in text, label
    assert "not the dimensional kernel" in readme
    assert "not the dimensional default" in status or "not the dimensional kernel" in status
    assert "not the dimensional default" in contributing or "not the dimensional kernel" in contributing
    assert "default backend" not in readme
    assert "not the default kernel" not in readme
    print("RESULT: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
