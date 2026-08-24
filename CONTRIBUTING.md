# Contributing to Agent Reach

Agent Reach is a capability layer, not a content wrapper. Contributions should
improve upstream-tool installation, secure configuration, health probing,
backend selection, or agent-facing guidance.

## Development

```bash
git clone https://github.com/Panniantong/Agent-Reach.git
cd Agent-Reach
python -m venv .venv
. .venv/bin/activate
python -m pip install -c constraints.txt -e ".[dev]"
bash test.sh
```

The release gate runs pytest, Ruff lint and formatting checks, mypy,
shellcheck, dependency auditing, a wheel build, and a clean wheel-install
smoke test. Tests must isolate `HOME`, network calls, browser state, and
subprocesses.

## Adding or changing a channel

1. Add or update its adapter in `agent_reach/channels/`.
2. Use a side-effect-free real probe and exact hostname/subdomain matching.
3. Declare ordered backends and per-capability readiness.
4. Register the channel type in `agent_reach/channels/__init__.py`.
5. Add hermetic success, missing, broken, timeout, fallback, and lookalike-host tests.
6. Update the packaged skill, all README locales, install/troubleshooting docs,
   `llms.txt`, and `CHANGELOG.md`.

Do not add native `read`, `search`, or platform-fetching methods. Agents call
the selected upstream tool directly.

## Security

Never commit real secrets or put secrets in command arguments. Preserve
read-only doctor/dry-run semantics, require explicit install consent, use
owner-only atomic writes, validate redirects/hosts, and treat fetched content
as untrusted. Report vulnerabilities according to [SECURITY.md](SECURITY.md).
