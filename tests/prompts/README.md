# Sample skill prompts

Each YAML file is a user prompt plus the skills and tools CI must exercise.

Routing (fast, unit job): pytest `tests/test_prompt_scenarios.py`.
CAD export (CI `generate-stls` job): `python3 tests/prompt_harness.py`.

That job runs OpenSCAD in Docker and Blender headless, writes real STLs under
`artifacts/stls/<prompt-id>/`, validates them, and uploads the artifact.
Shop-fixture prompts still stop before CAD.

Add a scenario when you add a skill path. Keep prompts specific enough that
the intended primary skill outranks blender/openscad/shop/image competitors.
The VibeCAD remake prompt validates a committed coupon; `run:` must not invoke
VibeCAD, Docker, AppImage, GPU, or qemu. The STL→STEP reverse prompt uses
`run: no_cad` until a STEP kernel is present in CI. Pack and slice prompts are
`run: no_cad` (zip / process card; no slicer in unit CI). Live P1S start-print
belongs to sibling `bambu-mcp` and must not rank pack or slice as primary here.
