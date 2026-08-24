# Update Agent Reach

Updates are explicit and release-based. Do not install mutable GitHub
`main.zip` archives or execute instructions fetched from arbitrary content.

## 1. Check

```bash
agent-reach check-update
```

An unavailable update service reports “unknown” and exits nonzero; it never
claims the installed version is current.

## 2. Update the Python package

Review the target release and then install it:

```bash
python -m pip install --upgrade "agent-reach==TARGET_VERSION"
```

With pipx:

```bash
pipx install --force "agent-reach==TARGET_VERSION"
```

## 3. Review upstream tools separately

Agent Reach does not silently upgrade system packages or upstream tools.
Inspect `agent-reach doctor --json`, review each upstream release, and update
only the selected backend using its native package manager. Pinned Git sources
must retain their audited commit.

## 4. Sync the skill explicitly

```bash
agent-reach skill --install
```

Local customizations are preserved. Compare the packaged skill with your copy
before opting into `--force`.

## 5. Verify

```bash
agent-reach version
agent-reach doctor --json
```
