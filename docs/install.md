# Install Agent Reach safely

Agent Reach is a capability layer. It prepares and diagnoses upstream tools;
afterward, the agent invokes those tools directly.

## Security contract

- The default `install` invocation is plan-only and makes no changes.
- `--dry-run`, `--safe`, and `doctor` create no files or directories.
- `--yes` is required for user-level package/configuration changes.
- Agent Reach never runs elevation, a system package manager, or a downloaded
  setup script. Missing GitHub CLI, Node.js, ffmpeg, and similar system tools
  are reported with platform-specific manual instructions.
- Never paste cookies/tokens/API keys into chat or command arguments. Use a
  hidden prompt, `--stdin`, or `--file`.

## 1. Install a released package

Use a reviewed release, not a mutable `main` archive:

```bash
python -m pip install "agent-reach==1.5.0"
```

For an isolated CLI:

```bash
pipx install "agent-reach==1.5.0"
```

## 2. Preview and approve

```bash
# Read-only plan
agent-reach install --env=auto

# More explicit read-only preview
agent-reach install --env=auto --dry-run

# Apply user-level changes after reviewing the plan
agent-reach install --env=auto --yes
```

Optional channels are opt-in:

```bash
agent-reach install --env=auto --channels=twitter,xiaoyuzhou --dry-run
agent-reach install --env=auto --channels=twitter,xiaoyuzhou --yes
```

OpenCLI requires a desktop Chrome session and a manual extension click.
Xiaoyuzhou's compatibility script is installed only when that channel is
selected. LinkedIn's MCP endpoint is `http://localhost:8001/mcp`.

## 3. Diagnose

```bash
agent-reach doctor
agent-reach doctor --json
```

Both forms are strictly read-only. JSON includes `active_backend` and explicit
per-capability readiness.

## 4. Configure without exposing secrets

Interactive prompts hide secret input:

```bash
agent-reach configure groq-key
agent-reach configure openai-key
agent-reach configure twitter-cookies
agent-reach configure github-token
```

Automation should use stdin:

```bash
printf '%s' "$GROQ_API_KEY" | agent-reach configure groq-key --stdin
printf '%s' "$TWITTER_COOKIE_HEADER" | agent-reach configure twitter-cookies --stdin
printf '%s' "$GH_TOKEN" | agent-reach configure github-token --stdin
```

The GitHub token is handed to `gh auth login --with-token`; Agent Reach keeps
no copy. Twitter credentials are stored owner-only and injected into Agent
Reach's health probe; direct `twitter` calls still need
`TWITTER_AUTH_TOKEN`/`TWITTER_CT0` in their process environment. YouTube
browser selection is written to the platform-correct yt-dlp config:

```bash
agent-reach configure youtube-cookies firefox
```

Browser auto-import persists only credentials with a verified consumer.
XiaoHongShu and Bilibili use OpenCLI/upstream login flows instead of unused
Agent Reach cookie keys.

## 5. Install or sync the packaged skill

```bash
agent-reach skill --install
```

Existing customized skill files are preserved. Review the diff before using
`agent-reach skill --install --force`.

## 6. Transcription privacy

`agent-reach transcribe` uploads audio to the selected Groq/OpenAI service.
Temporary audio is deleted on success and failure unless a caller explicitly
supplies an output work directory through the Python API.

## 7. Uninstall

```bash
agent-reach uninstall --dry-run
agent-reach uninstall
```

`--keep-config` keeps configuration and also leaves external mcporter entries
untouched. Upstream tools are never removed automatically.
