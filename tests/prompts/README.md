# Sample skill prompts

Each YAML file is a user prompt plus the skills and tools CI must exercise.

CI runs `python3 tests/run_prompt_scenarios.py` (also via pytest). No live model.
Routing is a keyword ranker over SKILL.md names, descriptions, tags, and body.
`run` steps execute the real spec/mesh tools, or assert policy-only stops.

Add a scenario when you add a skill path. Keep prompts specific enough that
the intended primary skill outranks blender/openscad/shop/image competitors.
