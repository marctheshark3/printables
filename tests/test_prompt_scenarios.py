from __future__ import annotations

from pathlib import Path

import pytest
import yaml

from prompt_harness import check_routing, load_scenarios, load_skills

SCENARIOS = load_scenarios()
CATALOG = load_skills()


@pytest.mark.parametrize("scenario", SCENARIOS, ids=lambda s: s["id"])
def test_prompt_routes_to_the_right_skill(scenario):
    ranked = check_routing(scenario, CATALOG)
    scores = dict(ranked)
    primary = scenario["expect"]["primary"]
    assert primary in scores
    for other in scenario["expect"].get("outrank", []):
        assert scores[primary] > scores[other]


def test_p1s_start_print_does_not_rank_pack_or_slice_primary():
    from prompt_harness import rank_skills

    ranked = rank_skills("start this print on the P1S", CATALOG)
    assert ranked[0][0] not in {"3d-print-pack", "3d-print-slice"}
    scores = dict(ranked)
    assert scores.get("3d-print-pack", 0) < scores[ranked[0][0]]
    assert scores.get("3d-print-slice", 0) < scores[ranked[0][0]]


def test_stl_to_step_bracket_run_is_no_cad():
    path = Path(__file__).resolve().parent / "prompts" / "stl-to-step-bracket.yaml"
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    assert data["expect"]["primary"] == "3d-print-reverse"
    for step in data["run"]:
        assert step["kind"] == "no_cad"


def test_vibecad_remake_run_steps_do_not_invoke_cad():
    path = Path(__file__).resolve().parent / "prompts" / "vibecad-remake.yaml"
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    assert data["expect"]["primary"] == "3d-print-vibecad"
    forbidden = ("docker", "appimage", "qemu", "gpu", "blender", "openscad", "vibecad_cmd")
    for step in data["run"]:
        assert step["kind"] in {"validate_spec", "validate_project"}
        blob = yaml.safe_dump(step).lower()
        assert not any(word in blob for word in forbidden)
