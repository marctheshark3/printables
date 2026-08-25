---
name: vibecad-printables
description: Use when remaking FDM parts in VibeCAD, not OpenSCAD.
version: 0.1.0
author: Marc Mailloux, Hermes Agent
license: MIT
platforms: [linux]
metadata:
  hermes:
    tags: [vibecad, freecad, 3d-print, printables, cad, dfm]
    related_skills: [printables-part-brief, printables-dfm-gate, openscad-printables]
---

# VibeCAD Printables

AI-native CAD fork of FreeCAD (`10-X-eng/vibecad`). Conversation + VibeScript/Native history. This skill is the **alternate CAD step**, not a replacement for intent or DFM.

Loop stays:

1. `printables-part-brief` → `docs/DESIGN.md`
2. **this skill** (or `openscad-printables`)
3. `printables-dfm-gate` — HARD fail = not done

Do **not** claim printable from a VibeCAD preview or a readable `.FCStd`.

## When to Use

- Marc points at <https://github.com/10-X-eng/vibecad> or says remake an existing printable in VibeCAD
- Headless/agent remake of gold OpenSCAD via Part CSG or VibeScript
- Wiring the loopback agent (Grok Bot / Hermes) against a running VibeCAD

**Don’t:** design shop cages (see `print-vs-buy-shop-fixtures`); skip DESIGN.md; enable MCP if Marc is using the in-app Assistant; confuse this with the unrelated PyPI package `vibecad` (wangtao9090 workbench).

## Lab location

`~/Documents/the-grid/vibecad-lab/` — AppImage, DESIGN.md, remake scripts, future `stl/` + `fcstd/`.

Official docs live in the upstream repo `docs/` (agent-control, authoring modes, MCP). Condensed: `references/agent-control.md`.

## Authoring modes (human-only)

Marc picks **VibeScript** or **Native** in the Assistant header. The model cannot switch modes or workbenches.

- **Native** — ribbon-frozen parametric tools, exact object IDs, one transaction per call
- **VibeScript** — source-backed program in one workbench domain; isolated worker; accepted source is authority

## Control surfaces

| Surface | Port / path | Use |
|---------|-------------|-----|
| In-app Assistant | GUI | Grok / ChatGPT / Anthropic after Preferences sign-in |
| Agent HTTP/CLI | `127.0.0.1:8766` | Open doc, run Python/VibeScript, status, Preferences |
| MCP | `127.0.0.1:8765/mcp` | **Disables** the in-app Assistant. Do not enable if Marc is chatting in-app |

Linux token/endpoint: `~/.local/share/VibeCAD/agent/` (`token` + `endpoint.json`). Override: `VIBECAD_AGENT_HOME`, `VIBECAD_AGENT_PORT`.

Agent must **never** type passwords or OAuth codes. Sign-in is Preferences only (browser or device-code).

## Procedure

1. Require `docs/DESIGN.md` (part-brief). Same product_class / orientation / never-list as OpenSCAD jobs.
2. Confirm launch consent before extracting or running the AppImage / GUI. No silent 900 MB extract.
3. Prefer remake scripts under `vibecad-lab/scripts/` (`remake_open_frame_coupon.py`, `remake_pan_l.py`, `remake_oak_foot.py`) over inventing new geometry.
4. Execute **inside** VibeCAD (`/v1/run` or `FreeCADCmd`/`VibeCADCmd` if present). Host Python has no `FreeCAD` module.
5. Export binary STL + save `.FCStd`. Report volume cm³, bbox, solid count.
6. Run `printables-dfm-gate` on the exported STL. HARD = not done.
7. Zip STL for Discord. Route new part design discussion to `#stl-design`; this skill lives in `#print-skills`.

## First remake set (gold → VibeCAD)

- open-frame coupon — `equipment-open-frame`, TOP-FIRST, posts outside chassis XY
- pan_L (+ stop-lip) — shop inner-corner for 1.5 in oak; do not print pan or post
- oak foot — square pocket `38.1 + 0.8`; not round; not 1×2

## Pitfalls

1. PyPI `vibecad` ≠ `10-X-eng/vibecad`
2. Enabling MCP kills the in-app Grok/ChatGPT assistant
3. Running remake scripts with Hermes `python3` (no FreeCAD bindings)
4. Shipping without DFM-gate
5. Pin forest / posts inside chassis XY / printing stock (pan, oak)
6. Launching the AppImage without Marc consent

## Verification

- [ ] DESIGN.md present
- [ ] STL written by VibeCAD/FreeCAD, not guessed
- [ ] dfm_gate HARD count = 0
- [ ] volume + orientation in the report
