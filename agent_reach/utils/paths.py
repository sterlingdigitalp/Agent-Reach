"""Cross-platform path and remediation helpers for yt-dlp."""

from __future__ import annotations

import os
import sys
from pathlib import Path

from agent_reach.utils.security import atomic_write_private_text


def get_ytdlp_config_dir() -> Path:
    """Return the recommended yt-dlp user config directory for this OS."""

    if sys.platform == "win32":
        appdata = os.environ.get("APPDATA")
        if appdata:
            return Path(appdata) / "yt-dlp"
        return Path.home() / "AppData" / "Roaming" / "yt-dlp"
    if sys.platform == "darwin":
        return Path.home() / "Library" / "Application Support" / "yt-dlp"
    return Path.home() / ".config" / "yt-dlp"


def get_ytdlp_config_path() -> Path:
    """Return the yt-dlp user config file path for this OS."""

    return get_ytdlp_config_dir() / "config"


def render_ytdlp_fix_command() -> str:
    """Return an OS-appropriate command to enable Node.js as yt-dlp JS runtime."""

    config_path = get_ytdlp_config_path()
    if sys.platform == "win32":
        return (
            f"$cfg = '{config_path}'\n"
            "New-Item -ItemType Directory -Force -Path (Split-Path $cfg) | Out-Null\n"
            "if (-not (Test-Path $cfg) -or -not (Select-String -Path $cfg -Pattern '--js-runtimes' -Quiet)) {\n"
            "  Add-Content -Path $cfg -Value '--js-runtimes node'\n"
            "}"
        )
    return (
        f"mkdir -p '{config_path.parent}' && "
        f"grep -qxF -- '--js-runtimes node' '{config_path}' 2>/dev/null || "
        f"printf '%s\n' '--js-runtimes node' >> '{config_path}'"
    )


def set_ytdlp_option(prefix: str, line: str) -> Path:
    """Idempotently set one option in the platform-correct yt-dlp config."""

    config_path = get_ytdlp_config_path()
    existing = ""
    if config_path.exists():
        existing = config_path.read_text(encoding="utf-8", errors="replace")
    kept = [item for item in existing.splitlines() if not item.strip().startswith(prefix)]
    kept.append(line)
    atomic_write_private_text(config_path, "\n".join(kept).rstrip() + "\n")
    return config_path
