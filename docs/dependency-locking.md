# Dependency policy

`constraints.txt` is the reviewed direct-dependency baseline used by CI. It is
not a complete cross-platform lock: environment markers and transitive wheels
can differ by Python version and operating system.

Runtime and development direct dependencies are pinned in
`constraints.txt`; the build backend is pinned in `pyproject.toml`. CI tests
Python 3.10–3.13, runs macOS/Windows smoke suites, audits the constraints, and
emits a CycloneDX SBOM.

For a deployment, resolve and retain a platform-specific lock with hashes
(for example `uv lock`/`uv export --generate-hashes` or
`pip-compile --generate-hashes`) and review the resulting transitive changes.
External npm/pipx/OS tools have independent release streams and must be
reviewed separately; Agent Reach does not claim that `constraints.txt` locks
them.
