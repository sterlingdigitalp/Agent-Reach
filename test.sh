#!/usr/bin/env bash
# Hermetic local release gate for the checked-out source tree.

set -euo pipefail

unset CDPATH
repo_root=$(cd -- "$(dirname -- "$0")" && pwd)
test_root=$(mktemp -d "${TMPDIR:-/tmp}/agent-reach-gate.XXXXXX")
trap 'rm -rf "$test_root"' EXIT HUP INT TERM

export HOME="$test_root/home"
export XDG_CONFIG_HOME="$HOME/.config"
export PYTHONPYCACHEPREFIX="$test_root/pycache"
mkdir -p "$HOME"

cd "$repo_root"

python -m pytest -q -p no:cacheprovider --cov=agent_reach --cov-report=term-missing
python -m ruff check agent_reach tests scripts
python -m ruff format --check agent_reach tests scripts
python -m mypy agent_reach

bash -n test.sh agent_reach/scripts/transcribe_xiaoyuzhou.sh
if command -v shellcheck >/dev/null 2>&1; then
    shellcheck test.sh agent_reach/scripts/transcribe_xiaoyuzhou.sh
else
    echo "shellcheck is required for the complete release gate" >&2
    exit 1
fi

python -m pip_audit -r constraints.txt --progress-spinner off
python -m build --wheel --outdir "$test_root/dist"
python -m venv "$test_root/smoke"
"$test_root/smoke/bin/python" -m pip install --no-deps "$test_root"/dist/*.whl
"$test_root/smoke/bin/agent-reach" version
"$test_root/smoke/bin/python" -c \
    "from importlib.resources import files; assert (files('agent_reach')/'skill'/'SKILL.md').is_file()"
"$test_root/smoke/bin/python" -c \
    "from importlib.metadata import entry_points; assert any(e.name == 'agent-reach-mcp' for e in entry_points(group='console_scripts'))"
