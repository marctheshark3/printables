#!/usr/bin/env python3
"""Run sample agent prompts against skill routing and the real CAD/CAM tools."""
from __future__ import annotations

import re
import shutil
import struct
import subprocess
import sys
import tempfile
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
PROMPTS = ROOT / "tests" / "prompts"
SKILLS = ROOT / "skills"
BUNDLE = ROOT / "skill-bundles" / "3d-print.yaml"

STOP = {
    "a", "an", "the", "for", "of", "to", "and", "or", "my", "i", "with", "from",
    "this", "that", "in", "on", "it", "be", "do", "not", "a", "then", "use",
    "before", "after", "into", "plus", "per", "one", "each", "need", "make",
    "build", "should", "than", "only",
}


def tokens(text: str) -> set[str]:
    return {t for t in re.findall(r"[a-z0-9]+", text.lower()) if t not in STOP and len(t) > 2}


def frontmatter_and_body(path: Path) -> tuple[dict, str]:
    text = path.read_text(encoding="utf-8")
    _, raw, body = text.split("---", 2)
    data = yaml.safe_load(raw)
    if not isinstance(data, dict):
        raise ValueError(f"{path}: frontmatter is not a mapping")
    return data, body


def load_skills() -> dict[str, dict]:
    catalog = {}
    for path in sorted(SKILLS.glob("*/SKILL.md")):
        meta, body = frontmatter_and_body(path)
        name = path.parent.name
        tags = meta.get("metadata", {}).get("hermes", {}).get("tags", [])
        catalog[name] = {
            "path": path,
            "meta": meta,
            "body": body,
            "corpus": {
                "name": tokens(name.replace("-", " ")),
                "desc": tokens(str(meta.get("description", ""))),
                "tags": tokens(" ".join(str(t) for t in tags)),
                "body": tokens(body[:5000]),
            },
        }
    return catalog


def score_prompt(prompt: str, corpus: dict[str, set[str]]) -> float:
    words = tokens(prompt)
    return (
        4.0 * len(words & corpus["name"])
        + 3.0 * len(words & corpus["desc"])
        + 3.0 * len(words & corpus["tags"])
        + 1.0 * len(words & corpus["body"])
    )


def rank_skills(prompt: str, catalog: dict[str, dict]) -> list[tuple[str, float]]:
    ranked = [(name, score_prompt(prompt, skill["corpus"])) for name, skill in catalog.items()]
    ranked.sort(key=lambda item: (-item[1], item[0]))
    return ranked


def write_cube(path: Path, size: float = 10.0) -> None:
    p = [
        (0, 0, 0), (size, 0, 0), (size, size, 0), (0, size, 0),
        (0, 0, size), (size, 0, size), (size, size, size), (0, size, size),
    ]
    faces = [
        (0, 2, 1), (0, 3, 2), (4, 5, 6), (4, 6, 7),
        (0, 1, 5), (0, 5, 4), (1, 2, 6), (1, 6, 5),
        (2, 3, 7), (2, 7, 6), (3, 0, 4), (3, 4, 7),
    ]
    path.parent.mkdir(parents=True, exist_ok=True)
    data = bytearray(80)
    data.extend(struct.pack("<I", len(faces)))
    for a, b, c in faces:
        data.extend(struct.pack("<12fH", 0, 0, 0, *p[a], *p[b], *p[c], 0))
    path.write_bytes(data)


def run_cmd(argv: list[str], cwd: Path | None = None) -> subprocess.CompletedProcess:
    return subprocess.run(argv, cwd=cwd, text=True, capture_output=True, check=False)


def validate_spec(path: Path, check_files: bool = False) -> None:
    cmd = [
        sys.executable,
        str(ROOT / "skills/3d-print-design-brief/scripts/validate_print_spec.py"),
        str(path),
    ]
    if check_files:
        cmd.append("--check-files")
    result = run_cmd(cmd)
    if result.returncode:
        raise AssertionError(
            f"validate_print_spec failed {path}\n{result.stdout}\n{result.stderr}"
        )


def validate_project(project: Path) -> None:
    result = run_cmd(
        [
            sys.executable,
            str(ROOT / "skills/3d-print-validate/scripts/validate_project.py"),
            str(project),
        ]
    )
    if result.returncode:
        raise AssertionError(
            f"validate_project failed {project}\n{result.stdout}\n{result.stderr}"
        )


def spec_template(
    *,
    name: str,
    product_class: str,
    backend: str,
    source_files: list[str],
    bodies: list[dict],
    parameters: list[dict],
) -> dict:
    dims = []
    for item in parameters:
        dims.append({
            "name": item["name"],
            "parameter": item["parameter"],
            "value_mm": item["value_mm"],
            "tolerance_mm": item.get("tolerance_mm", 0.2),
            "source": item.get("source", "measured"),
        })
    return {
        "schema_version": 1,
        "part": {
            "name": name,
            "revision": "0.1.0",
            "product_class": product_class,
            "purpose": f"Prompt-scenario {name}",
        },
        "manufacturing": {
            "process": "fdm",
            "printer": "generic-256mm",
            "build_volume_mm": [256, 256, 256],
            "material": "PETG",
            "nozzle_mm": 0.4,
            "layer_height_mm": 0.2,
        },
        "cad": {
            "backend": backend,
            "parametric": True,
            "units": "mm",
            "source_files": source_files,
        },
        "geometry": {
            "min_wall_mm": 1.6,
            "min_feature_mm": 1.6,
            "overlapping_solids_allowed": False,
            "stl_files": bodies,
        },
        "fit": {
            "required": False,
            "clearance_per_side_mm": 0.4,
            "evidence": "none",
            "coupon": "not-required",
        },
        "dimensions": dims,
        "print": {
            "orientation": "base-on-bed",
            "bed_face": "bottom",
            "up_axis": "Z",
            "supports": "none",
            "max_overhang_deg": 45,
        },
        "service": {"environment": "dry", "drainage": "not-applicable"},
    }


def run_step(step: dict, catalog: dict[str, dict]) -> str:
    kind = step["kind"]
    if kind == "validate_spec":
        validate_spec(ROOT / step["path"])
        return f"validate_spec {step['path']}"

    if kind == "project_with_cubes":
        src = ROOT / step["from"]
        with tempfile.TemporaryDirectory() as td:
            dest = Path(td) / src.name
            shutil.copytree(src, dest)
            spec_path = dest / "docs" / "PRINT_SPEC.yaml"
            data = yaml.safe_load(spec_path.read_text(encoding="utf-8"))
            for body in data["geometry"]["stl_files"]:
                write_cube(dest / body["path"])
            validate_project(dest)
        return f"project_with_cubes {step['from']}"

    if kind == "synthetic_assembly":
        with tempfile.TemporaryDirectory() as td:
            project = Path(td) / "assembly"
            (project / "docs").mkdir(parents=True)
            (project / "src").mkdir()
            (project / "stl").mkdir()
            for rel, text in step["sources"].items():
                path = project / rel
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text(text, encoding="utf-8")
            bodies = step["bodies"]
            spec = spec_template(
                name="prompt-assembly",
                product_class=step["product_class"],
                backend=step.get("backend", "openscad"),
                source_files=list(step["sources"]),
                bodies=bodies,
                parameters=step["parameters"],
            )
            (project / "docs" / "PRINT_SPEC.yaml").write_text(
                yaml.safe_dump(spec, sort_keys=False), encoding="utf-8"
            )
            for body in bodies:
                write_cube(project / body["path"])
            validate_project(project)
        return "synthetic_assembly"

    if kind == "pblend_new":
        cli = ROOT / "skills/3d-print-blender/scripts/pblend_cli.py"
        with tempfile.TemporaryDirectory() as td:
            result = run_cmd(
                [
                    sys.executable, str(cli), "new", step["name"],
                    "--root", td, "--class", step["product_class"],
                ]
            )
            if result.returncode:
                raise AssertionError(f"pblend new failed\n{result.stdout}\n{result.stderr}")
            project = Path(td) / step["name"]
            spec_path = project / "docs" / "PRINT_SPEC.yaml"
            validate_spec(spec_path)
            data = yaml.safe_load(spec_path.read_text(encoding="utf-8"))
            for body in data["geometry"]["stl_files"]:
                write_cube(project / body["path"])
            validate_project(project)
        return f"pblend_new {step['name']}"

    if kind == "no_cad":
        return f"no_cad ({step.get('reason', 'policy stop')})"

    if kind == "scripts_exist":
        missing = [p for p in step["paths"] if not (ROOT / p).is_file()]
        if missing:
            raise AssertionError(f"missing scripts: {missing}")
        return f"scripts_exist {len(step['paths'])}"

    raise AssertionError(f"unknown step kind: {kind}")


def check_routing(scenario: dict, catalog: dict[str, dict]) -> list[tuple[str, float]]:
    expect = scenario["expect"]
    prompt = scenario["prompt"]
    ranked = rank_skills(prompt, catalog)
    scores = dict(ranked)
    primary = expect["primary"]
    if primary not in catalog:
        raise AssertionError(f"unknown primary skill {primary}")
    for name in expect.get("skills", []):
        if name not in catalog:
            raise AssertionError(f"unknown expected skill {name}")
    for other in expect.get("outrank", []):
        if scores.get(primary, 0) <= scores.get(other, 0):
            raise AssertionError(
                f"{primary} score {scores.get(primary, 0)} did not outrank "
                f"{other} score {scores.get(other, 0)}\nrank={ranked}"
            )
    bundle_name = expect.get("bundle")
    if bundle_name:
        bundle = yaml.safe_load(BUNDLE.read_text(encoding="utf-8"))
        if bundle["name"] != bundle_name:
            raise AssertionError(f"bundle name {bundle['name']} != {bundle_name}")
        core = {"3d-print-design-brief", "3d-print-openscad", "3d-print-blender", "3d-print-validate"}
        missing_core = [s for s in expect.get("skills", []) if s in core and s not in bundle["skills"]]
        if missing_core:
            raise AssertionError(f"bundle {bundle_name} missing {missing_core}")
    for skill_name, needles in expect.get("skill_contains", {}).items():
        text = catalog[skill_name]["path"].read_text(encoding="utf-8")
        missing = [n for n in needles if not isinstance(n, str) or n not in text]
        if any(not isinstance(n, str) for n in needles):
            raise AssertionError(f"{skill_name} skill_contains values must be strings, got {needles}")
        if missing:
            raise AssertionError(f"{skill_name} missing required procedure text: {missing}")
    return ranked


def load_scenarios() -> list[dict]:
    scenarios = []
    for path in sorted(PROMPTS.glob("*.yaml")):
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
        data["_path"] = path
        scenarios.append(data)
    if not scenarios:
        raise AssertionError(f"no prompt scenarios in {PROMPTS}")
    return scenarios


def run_scenario(scenario: dict, catalog: dict[str, dict] | None = None) -> str:
    catalog = catalog or load_skills()
    ranked = check_routing(scenario, catalog)
    lines = [
        f"PROMPT {scenario['id']}",
        "  " + " ".join(scenario["prompt"].split()),
        "  ROUTE " + " > ".join(f"{name}={score:.1f}" for name, score in ranked[:5]),
    ]
    for step in scenario.get("run", []):
        label = run_step(step, catalog)
        lines.append(f"  RUN {label} PASS")
    return "\n".join(lines)


def main() -> int:
    catalog = load_skills()
    failed = 0
    for scenario in load_scenarios():
        try:
            print(run_scenario(scenario, catalog))
            print()
        except Exception as exc:
            failed += 1
            print(f"PROMPT {scenario['id']} FAIL: {exc}\n")
    if failed:
        print(f"RESULT: FAIL ({failed} prompt scenarios)")
        return 1
    print("RESULT: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
