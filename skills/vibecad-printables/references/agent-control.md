# VibeCAD agent control (condensed)

Upstream: `docs/vibecad-agent-control.md`, `docs/vibecad-authoring-modes.md` in `10-X-eng/vibecad`.

## What this channel is

Scriptable control for a desktop agent that cannot click menus. It does **not** replace the in-app Assistant and it does **not** turn MCP on.

Use it to: open a saved document, run Python or VibeScript against the active doc, show Preferences, read provider/auth status (no secrets).

## Endpoints

- GUI already up → loopback HTTP `127.0.0.1:8766` (Bearer token) or the Python CLI as an HTTP client
- Headless → `FreeCADCmd` / `VibeCADCmd` with the agent CLI `--local` if present
- MCP `http://127.0.0.1:8765/mcp` is mutually exclusive. Enabling MCP **disables** the in-app Assistant.

Linux agent home: `~/.local/share/VibeCAD/agent/`
- `token` — read it; do not prompt a human
- `endpoint.json` — `host`, `port`, `base_url`, `token_path` (no token inside)

Overrides: `VIBECAD_AGENT_HOME`, `VIBECAD_AGENT_PORT`.

## Routes (all loopback + Bearer)

| Method | Path | Body |
|--------|------|------|
| GET | `/v1/status` | provider, auth flags, documents |
| GET | `/v1/documents` | open docs |
| POST | `/v1/open` | `{"path":"...FCStd"}` |
| POST | `/v1/run` | `{"python":"..."}` or `{"script":"..."}` + optional `path`, `recompute` |
| POST | `/v1/preferences` | GUI-only; headless returns `GUI_REQUIRED` |

`run` executes as Python with `App`/`FreeCAD` (and `Gui` when GUI is up). Assign `result` or `__result__` for JSON. VibeScript files are the same: Python against the active document.

## Auth (in-app)

Preferences → VibeCAD → enable online provider.

- **Grok (X / xAI)** — Sign in with X / Grok or device-code. Needs SuperGrok or linked X Premium+. OAuth issuer `https://auth.x.ai`. HTTP 403 after login → API-key fallback: provider OpenAI/Codex, base URL `https://api.x.ai/v1`.
- ChatGPT subscription, Anthropic, OpenAI-compatible (incl. Ollama / LiteLLM) also work.

Never type passwords or device codes. Never import ambient Codex tokens from another install.

## Releases (Linux)

Latest checked: `v26.3.1-RC5-build1` AppImage + `.deb` on GitHub Releases. Verify SHA256 beside the artifact. Lab copy: `~/Documents/the-grid/vibecad-lab/`.

## House remake scripts

`~/Documents/the-grid/vibecad-lab/scripts/`

- `remake_open_frame_coupon.py`
- `remake_pan_l.py`
- `remake_oak_foot.py`

These import `FreeCAD`, `Part`, `Mesh` — they only run inside VibeCAD. After STL export, `printables-dfm-gate`.
