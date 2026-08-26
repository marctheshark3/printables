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
    "3d-print-validate",
    "3d-print-display-enclosure",
    "3d-print-image-silhouette",
    "3d-print-shop-fixture",
    "3d-print-robotics",
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
    print("RESULT: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
