#!/usr/bin/env python3
"""Run sample agent prompts against skill routing and the real CAD/CAM tools."""
from __future__ import annotations

import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
PROMPTS = ROOT / "tests" / "prompts"
SKILLS = ROOT / "skills"
BUNDLE = ROOT / "skill-bundles" / "3d-print.yaml"
OPENSCAD_IMAGE = os.environ.get("OPENSCAD_IMAGE", "openscad/openscad:2021.01")
STL_OUT = Path(os.environ.get("PRINTABLES_STL_OUT", str(ROOT / "artifacts" / "stls")))
REQUIRE_CAD = os.environ.get("PRINTABLES_GENERATE_STLS") == "1" or os.environ.get("CI") == "true"


class CadMissing(RuntimeError):
    pass

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


def run_cmd(
    argv: list[str], cwd: Path | None = None, env: dict | None = None
) -> subprocess.CompletedProcess:
    return subprocess.run(argv, cwd=cwd, text=True, capture_output=True, check=False, env=env)


def collect_stls(project: Path, scenario_id: str) -> list[str]:
    dest = STL_OUT / scenario_id
    dest.mkdir(parents=True, exist_ok=True)
    names = []
    for stl in sorted(project.glob("stl/*.stl")):
        if stl.stat().st_size < 84:
            raise AssertionError(f"empty or invalid STL: {stl}")
        shutil.copy2(stl, dest / stl.name)
        names.append(stl.name)
    if not names:
        raise AssertionError(f"no STLs produced under {project / 'stl'}")
    return names


def cad_or_raise(tool: str) -> None:
    raise CadMissing(f"{tool} is required to generate STLs")


_DOCKER: bool | None = None


def have_docker() -> bool:
    global _DOCKER
    if _DOCKER is None:
        _DOCKER = bool(shutil.which("docker") and run_cmd(["docker", "info"]).returncode == 0)
    return _DOCKER


def find_blender() -> str | None:
    env = os.environ.get("BLENDER")
    if env and Path(env).is_file():
        return env
    return shutil.which("blender")


def export_openscad(project: Path, src_rel: str, stl_rel: str, defines: dict | None = None) -> None:
    src = project / src_rel
    out = project / stl_rel
    if not src.is_file():
        raise AssertionError(f"missing OpenSCAD source {src}")
    out.parent.mkdir(parents=True, exist_ok=True)
    define_args: list[str] = []
    for key, value in (defines or {}).items():
        if isinstance(value, str):
            define_args.extend(["-D", f'{key}="{value}"'])
        else:
            define_args.extend(["-D", f"{key}={value}"])
    if have_docker():
        cmd = [
            "docker", "run", "--rm",
            "--user", f"{os.getuid()}:{os.getgid()}",
            "-v", f"{project.resolve()}:/work",
            "-w", "/work",
            OPENSCAD_IMAGE,
            "openscad", "-o", f"/work/{stl_rel}",
            "--export-format=binstl",
            *define_args,
            f"/work/{src_rel}",
        ]
    elif shutil.which("openscad"):
        cmd = [
            "openscad", "-o", str(out), "--export-format=binstl",
            *define_args, str(src),
        ]
    else:
        cad_or_raise("docker OpenSCAD or openscad")
        return
    result = run_cmd(cmd)
    if result.returncode or not out.is_file() or out.stat().st_size < 84:
        raise AssertionError(
            f"OpenSCAD export failed {src_rel} -> {stl_rel}\n{result.stdout}\n{result.stderr}"
        )


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


def skip_or_fail(exc: CadMissing) -> str:
    if REQUIRE_CAD:
        raise AssertionError(str(exc)) from exc
    return f"SKIP ({exc})"


def write_project_spec(project: Path, step: dict) -> None:
    bodies = [{k: v for k, v in body.items() if k != "define"} for body in step["bodies"]]
    spec = spec_template(
        name=step.get("name", "prompt-assembly"),
        product_class=step["product_class"],
        backend=step.get("backend", "openscad"),
        source_files=list(step["sources"]),
        bodies=bodies,
        parameters=step["parameters"],
    )
    (project / "docs" / "PRINT_SPEC.yaml").write_text(
        yaml.safe_dump(spec, sort_keys=False), encoding="utf-8"
    )


def run_step(step: dict, catalog: dict[str, dict], scenario_id: str) -> str:
    kind = step["kind"]
    if kind == "validate_spec":
        validate_spec(ROOT / step["path"])
        return f"validate_spec {step['path']}"

    if kind == "export_openscad_project":
        src = ROOT / step["from"]
        try:
            with tempfile.TemporaryDirectory() as td:
                dest = Path(td) / src.name
                shutil.copytree(src, dest)
                spec_path = dest / "docs" / "PRINT_SPEC.yaml"
                validate_spec(spec_path)
                data = yaml.safe_load(spec_path.read_text(encoding="utf-8"))
                source = data["cad"]["source_files"][0]
                for body in data["geometry"]["stl_files"]:
                    export_openscad(dest, source, body["path"])
                names = collect_stls(dest, scenario_id)
                validate_project(dest)
            return f"export_openscad_project {step['from']} stls={names}"
        except CadMissing as exc:
            return skip_or_fail(exc)

    if kind == "export_openscad_assembly":
        try:
            with tempfile.TemporaryDirectory() as td:
                project = Path(td) / "assembly"
                (project / "docs").mkdir(parents=True)
                (project / "src").mkdir()
                (project / "stl").mkdir()
                for rel, text in step["sources"].items():
                    path = project / rel
                    path.parent.mkdir(parents=True, exist_ok=True)
                    path.write_text(text, encoding="utf-8")
                write_project_spec(project, step)
                validate_spec(project / "docs" / "PRINT_SPEC.yaml")
                source = next(iter(step["sources"]))
                for body in step["bodies"]:
                    export_openscad(project, source, body["path"], body.get("define"))
                names = collect_stls(project, scenario_id)
                validate_project(project)
            return f"export_openscad_assembly stls={names}"
        except CadMissing as exc:
            return skip_or_fail(exc)

    if kind == "export_blender_project":
        blender = find_blender()
        if not blender:
            return skip_or_fail(CadMissing("blender"))
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
            validate_spec(project / "docs" / "PRINT_SPEC.yaml")
            exported = run_cmd(
                [sys.executable, str(cli), "run", "--project", str(project), "--blender", blender]
            )
            if exported.returncode:
                raise AssertionError(
                    f"pblend run failed\n{exported.stdout}\n{exported.stderr}"
                )
            names = collect_stls(project, scenario_id)
            validate_project(project)
        return f"export_blender_project {step['name']} stls={names}"

    if kind == "export_image_stencil":
        try:
            from PIL import Image, ImageDraw
        except ImportError:
            return skip_or_fail(CadMissing("Pillow"))
        try:
            with tempfile.TemporaryDirectory() as td:
                project = Path(td) / step["name"]
                source = project / "source"
                trace = project / "trace" / step["name"]
                (project / "docs").mkdir(parents=True)
                (project / "src").mkdir()
                (project / "stl").mkdir()
                source.mkdir(parents=True)
                icon = source / "icon.png"
                img = Image.new("RGB", (400, 400), "white")
                draw = ImageDraw.Draw(img)
                draw.ellipse((80, 80, 320, 320), fill="black")
                img.save(icon)
                traced = run_cmd(
                    [
                        sys.executable,
                        str(ROOT / "skills/3d-print-image-silhouette/scripts/trace_silhouette.py"),
                        "--input", str(icon),
                        "--out-dir", str(trace),
                        "--plate", str(step["plate_mm"]),
                        "--frame", str(step["frame_mm"]),
                        "--min-feature-mm", "1.6",
                        "--hole-policy", "filled",
                    ]
                )
                if traced.returncode:
                    raise AssertionError(f"trace failed\n{traced.stdout}\n{traced.stderr}")
                overlay = run_cmd(
                    [
                        sys.executable,
                        str(ROOT / "skills/3d-print-image-silhouette/scripts/overlay_preview.py"),
                        "--poly", str(trace / "poly.json"),
                        "--out", str(trace / "overlay.png"),
                    ]
                )
                if overlay.returncode:
                    raise AssertionError(f"overlay failed\n{overlay.stdout}\n{overlay.stderr}")
                scad = project / "src" / f"{step['name']}.scad"
                made = run_cmd(
                    [
                        sys.executable,
                        str(ROOT / "skills/3d-print-image-silhouette/scripts/scad_from_poly.py"),
                        "--poly", str(trace / "poly.json"),
                        "--out", str(scad),
                        "--name", step["name"],
                        "--thickness", str(step["thickness_mm"]),
                    ]
                )
                if made.returncode:
                    raise AssertionError(f"scad_from_poly failed\n{made.stdout}\n{made.stderr}")
                spec = spec_template(
                    name=step["name"],
                    product_class="silhouette",
                    backend="openscad",
                    source_files=[f"src/{step['name']}.scad"],
                    bodies=[{
                        "path": f"stl/{step['name']}.stl",
                        "body": "stencil",
                        "expected_shells": 1,
                    }],
                    parameters=[
                        {"name": "plate", "parameter": "plate", "value_mm": step["plate_mm"]},
                        {"name": "thickness", "parameter": "thickness", "value_mm": step["thickness_mm"]},
                        {"name": "frame", "parameter": "frame", "value_mm": step["frame_mm"]},
                    ],
                )
                (project / "docs" / "PRINT_SPEC.yaml").write_text(
                    yaml.safe_dump(spec, sort_keys=False), encoding="utf-8"
                )
                validate_spec(project / "docs" / "PRINT_SPEC.yaml")
                export_openscad(project, f"src/{step['name']}.scad", f"stl/{step['name']}.stl")
                names = collect_stls(project, scenario_id)
                validate_project(project)
            return f"export_image_stencil stls={names}"
        except CadMissing as exc:
            return skip_or_fail(exc)

    if kind == "no_cad":
        return f"no_cad ({step.get('reason', 'policy stop')})"

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
        label = run_step(step, catalog, scenario["id"])
        lines.append(f"  RUN {label}")
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
