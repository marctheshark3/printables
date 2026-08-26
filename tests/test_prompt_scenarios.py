from __future__ import annotations

import pytest

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
