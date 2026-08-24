# Agent Reach

Agent Reach gives AI agents diagnosed access to 13 internet platforms through
upstream tools. It is a capability layer—not a unified read/search wrapper.
After `agent-reach doctor --json` selects an active backend, the agent calls
that backend directly.

## Channels

| Channel | Preferred capability |
|---|---|
| GitHub | `gh` CLI |
| Twitter/X | twitter-cli, OpenCLI, bird fallback |
| YouTube | yt-dlp |
| Reddit | OpenCLI or rdt-cli; login required |
| Bilibili | bili-cli, OpenCLI, limited search API fallback |
| XiaoHongShu | OpenCLI or xiaohongshu-mcp |
| LinkedIn | linkedin-scraper-mcp; Jina read-only fallback |
| Xiaoyuzhou | Groq/OpenAI transcription with ffmpeg |
| V2EX | public API |
| Xueqiu | authenticated API cookie |
| RSS | feedparser |
| Exa Search | Exa MCP through mcporter; no API key |
| Web | Jina Reader |

Health JSON reports channel status, `active_backend`, and readiness separately
for each declared capability. A limited fallback is degraded, not “fully
available.”

## Safe installation

Install a reviewed release:

```bash
python -m pip install "agent-reach==1.5.0"
```

Preview first; the default is read-only:

```bash
agent-reach install --env=auto
agent-reach install --env=auto --dry-run
```

Apply user-level changes only after review:

```bash
agent-reach install --env=auto --yes
agent-reach install --env=auto --channels=twitter,xiaoyuzhou --yes
```

Agent Reach never runs elevation, system package managers, or downloaded setup
scripts. `doctor`, `--dry-run`, and plan mode create no state.

## Credentials

Never place cookies or API keys in command arguments, shell history, agent
chat, or logs. Use a hidden prompt or stdin:

```bash
agent-reach configure groq-key
printf '%s' "$GROQ_API_KEY" | agent-reach configure groq-key --stdin
printf '%s' "$GH_TOKEN" | agent-reach configure github-token --stdin
```

Secret-bearing Agent Reach files are replaced atomically with owner-only
permissions, including legacy files that were previously 0644. GitHub tokens
are stored by `gh`, not Agent Reach. See [the install guide](install.md) for
the key-to-consumer map.

## Diagnosis and skill

```bash
agent-reach doctor
agent-reach doctor --json
agent-reach skill --install
```

Doctor is strictly read-only. Skill installation is explicit and preserves
local customizations unless `--force` is requested.

The packaged skill is fetch-only. It treats retrieved content as untrusted,
does not accept embedded instructions, validates exact hosts, bounds output,
protects credentials, and requires separate authorization for every write.

## Privacy

Most upstream reads go directly to the named service. Transcription uploads
audio to the configured Groq/OpenAI provider and discloses that transfer before
running. Temporary audio is deleted on success or failure by default.

## Development

```bash
python -m pip install -c constraints.txt -e ".[dev]"
bash test.sh
```

The release gate includes pytest, Ruff, formatting, mypy, shellcheck,
dependency audit, secret-pattern scan, wheel build, and clean-install smoke
tests. See [CONTRIBUTING.md](../CONTRIBUTING.md).
