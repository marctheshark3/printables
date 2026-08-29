# Security

Do not file issues or PRs that include:

- API keys, GitHub tokens, Discord webhooks
- VibeCAD / CAD assistant OAuth codes or `token` files
- Private hub URLs, Tailscale hostnames, home addresses
- Photos of people or a household interior

If you believe a secret landed in git history, **stop and rotate** the credential. A later delete commit is not enough.

This repository has no required GitHub Actions secrets. Workflows use `permissions: contents: read`.

Printer identity for the sibling `bambu-mcp` server (`BAMBU_IP`, `BAMBU_ACCESS_CODE`, `BAMBU_SERIAL`) stays in env / user config. Never commit `.env`, access codes, serials, or LAN IPs. If a printer secret lands in history, stop and rotate the access code.
