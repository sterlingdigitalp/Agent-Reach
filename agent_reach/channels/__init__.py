# -*- coding: utf-8 -*-
"""
Channel registry — lists all supported platforms for doctor checks.
"""

from .base import Channel
from .bilibili import BilibiliChannel
from .exa_search import ExaSearchChannel
from .github import GitHubChannel
from .linkedin import LinkedInChannel
from .reddit import RedditChannel
from .rss import RSSChannel
from .twitter import TwitterChannel
from .v2ex import V2EXChannel

# Import all channels
from .web import WebChannel
from .youtube import YouTubeChannel

ALL_CHANNEL_TYPES: tuple[type[Channel], ...] = (
    GitHubChannel,
    TwitterChannel,
    YouTubeChannel,
    RedditChannel,
    BilibiliChannel,
    LinkedInChannel,
    V2EXChannel,
    RSSChannel,
    ExaSearchChannel,
    WebChannel,
)


def get_channel(name: str) -> Channel | None:
    """Get a fresh channel instance by name."""
    for channel_type in ALL_CHANNEL_TYPES:
        if channel_type.name == name:
            return channel_type()
    return None


def get_all_channels() -> list[Channel]:
    """Get request-scoped channel instances.

    Channel checks record ``active_backend``. Returning fresh objects avoids
    leaking that mutable state across doctor calls, threads, or MCP requests.
    """

    return [channel_type() for channel_type in ALL_CHANNEL_TYPES]


__all__ = [
    "Channel",
    "ALL_CHANNEL_TYPES",
    "get_channel",
    "get_all_channels",
]
