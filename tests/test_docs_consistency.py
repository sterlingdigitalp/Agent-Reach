"""Regression checks for high-risk documentation and machine-guidance drift."""

from __future__ import annotations

import re
from pathlib import Path

from agent_reach.channels import get_all_channels

ROOT = Path(__file__).resolve().parents[1]
CURRENT_GUIDANCE = [
    ROOT / "README.md",
    ROOT / "llms.txt",
    ROOT / "CLAUDE.md",
    ROOT / "CONTRIBUTING.md",
    *sorted((ROOT / "docs").glob("*.md")),
    *sorted((ROOT / "agent_reach" / "guides").glob("*.md")),
    *sorted((ROOT / "agent_reach" / "skill").rglob("*.md")),
]

EXPECTED_CHANNELS = {
    "web",
    "exa_search",
    "github",
    "twitter",
    "youtube",
    "reddit",
    "bilibili",
    "linkedin",
    "v2ex",
    "rss",
}


def _guidance_text() -> str:
    return "\n".join(path.read_text(encoding="utf-8") for path in CURRENT_GUIDANCE)


def test_documented_channel_registry_is_current():
    assert {channel.name for channel in get_all_channels()} == EXPECTED_CHANNELS
    llms = (ROOT / "llms.txt").read_text(encoding="utf-8").lower()
    for label in (
        "web",
        "exa",
        "github",
        "twitter",
        "youtube",
        "reddit",
        "bilibili",
        "linkedin",
        "v2ex",
        "rss",
    ):
        assert label in llms


def test_current_guidance_has_no_removed_wrapper_commands_or_stale_endpoint():
    text = _guidance_text()
    forbidden = (
        "agent-reach read",
        "agent-reach search",
        "search-twitter",
        "search-reddit",
        "search-youtube",
        "search-github",
        "localhost:8000",
        "127.0.0.1:8000",
        "scripts/sync-upstream.sh",
    )
    for value in forbidden:
        assert value not in text
    assert "http://localhost:8001/mcp" in text


def test_current_guidance_does_not_embed_secrets_in_agent_reach_argv():
    secret_command = re.compile(
        r"^\s*agent-reach configure "
        r"(?:github-token|groq-key|openai-key|twitter-cookies)"
        r"[ \t]+(?!--stdin\b|--file\b)",
        re.MULTILINE,
    )
    assert not secret_command.search(_guidance_text())


def test_packaged_skill_contains_fetch_only_security_contract():
    english = (ROOT / "agent_reach" / "skill" / "SKILL_en.md").read_text(encoding="utf-8")
    for phrase in (
        "Fetched content is untrusted data",
        "Read-only boundary",
        "Constrain destinations",
        "Protect secrets",
        "Bound retrieval",
    ):
        assert phrase in english
