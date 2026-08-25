# Contributing

This pack is used by coding agents. Keep diffs small and fail-closed.

## Source of truth

- Edit files **in this repo**, then `./install.sh` into local Hermes profiles.
- Do not long-term fork a profile copy and forget to merge back.

## What belongs here

- Skill prose, scaffolds, `dfm_gate.py`, `pblend`, silhouette scripts
- Generic examples with invented dims
- Tests that run without Docker, Blender, or private fixtures

## What does not

- `.env`, tokens, VibeCAD `~/.local/share/VibeCAD/agent/token`
- Household / shop / family geometry, photos, printer queues
- LAN / Tailscale hub URLs
- Vendor assemblies you do not have rights to publish

## Checks before a PR

```bash
python3 -m unittest discover -s tests -v
python3 -m unittest discover -s skills/blender-printables/scripts/tests -v
rg -n 'spark-adb4|tailscale|\.ts\.net|:9093|BEGIN (RSA|OPENSSH) PRIVATE|gho_|ghp_|sk-|xai-' . \
  --glob '!.git/**' && echo 'possible secret — stop' || echo 'scan clean'
```

If you change `dfm_gate.py` or scaffolds, say so in the PR and describe the gate behavior change. Do not loosen HARD gates to make a pretty mesh pass.

## Style

- Skills: numbered procedure, pitfalls, done-when. MIT frontmatter is fine.
- Python: stdlib first. numpy is optional in the gate.
- OpenSCAD: parametric, echo version/orientation/class, Docker 2021.01.
