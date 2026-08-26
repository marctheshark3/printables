from __future__ import annotations

import pytest

from prompt_harness import load_scenarios, load_skills, run_scenario

SCENARIOS = load_scenarios()
CATALOG = load_skills()


@pytest.mark.parametrize("scenario", SCENARIOS, ids=lambda s: s["id"])
def test_prompt_scenario(scenario):
    report = run_scenario(scenario, CATALOG)
    assert scenario["id"] in report
    assert "ROUTE" in report
