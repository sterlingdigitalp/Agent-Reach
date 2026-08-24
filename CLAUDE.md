# Repository guidance

Agent Reach is a Python capability layer for upstream internet tools. Preserve
the boundary: Agent Reach installs, configures, diagnoses, and documents
backends; agents invoke those backends directly. Do not add unified
read/search routing or copied platform fetchers.

## Local gates

Install the pinned development set, then run:

```bash
python -m pip install -c constraints.txt -e ".[dev]"
python -m pytest -q
python -m ruff check agent_reach tests
python -m ruff format --check agent_reach tests
python -m mypy agent_reach
bash -n test.sh
shellcheck test.sh
python -m pip_audit -r constraints.txt --progress-spinner off
```

`bash test.sh` runs the complete checkout-based release gate. It never installs
remote `main` or invokes removed wrapper commands.

## Architecture

- `agent_reach/channels/`: one health adapter per platform.
- `agent_reach/backends/`: shared multi-platform runtimes such as OpenCLI.
- `agent_reach/doctor.py`: bounded, concurrent, read-only health aggregation.
- `agent_reach/config.py`: schema-versioned owner-only local configuration.
- `agent_reach/skill/`: packaged fetch-only runtime instructions.
- `agent_reach/cli.py`: command dispatch and remaining command implementations.

Channel probes must be side-effect-free, execute a real lightweight operation,
set `active_backend` truthfully, expose per-capability readiness, use exact-host
matching, and include hermetic tests. Register new channels in
`agent_reach/channels/__init__.py` and update every README/skill reference.

Never put credentials in argv, logs, fixtures, or docs. Installers require
explicit consent and must not run elevation, system package managers, mutable
remote scripts, or unverified downloads.
