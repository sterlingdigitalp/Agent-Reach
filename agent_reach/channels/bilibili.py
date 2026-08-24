# -*- coding: utf-8 -*-
"""Bilibili — credential-free public search API only.

This channel is deliberately reduced to the logged-out search API. The
former bili-cli backend (unmaintained upstream since 2026-03) and the
OpenCLI browser-session backend (reuses your logged-in browser state)
were removed: this fork keeps Bilibili strictly as a zero-credential
search expander, never a cookie consumer.

yt-dlp was REMOVED from this channel earlier (live-verified 2026-06):
bilibili's risk control 412-blocks yt-dlp's requests in every
configuration tried. yt-dlp remains the YouTube backend only.
"""

import json
import urllib.request

from agent_reach.models import CapabilityReadiness
from agent_reach.utils.urls import host_matches

from .base import Channel

_UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
_TIMEOUT = 10
_SEARCH_API = "https://api.bilibili.com/x/web-interface/search/all/v2?keyword=test&page=1"


def _search_api_ok() -> bool:
    """Return True if Bilibili search API responds with code 0."""
    req = urllib.request.Request(_SEARCH_API, headers={"User-Agent": _UA})
    try:
        with urllib.request.urlopen(req, timeout=_TIMEOUT) as resp:
            data = json.loads(resp.read())
            return data.get("code") == 0
    except Exception:
        return False


class BilibiliChannel(Channel):
    name = "bilibili"
    description = "B站公开搜索（无凭据、无登录态）"
    backends = ["B站搜索 API"]
    tier = 1
    network = True  # probe makes an outbound request
    capabilities = ("search",)

    def can_handle(self, url: str) -> bool:
        return host_matches(url, "bilibili.com", "b23.tv")

    def check(self, config=None):
        """Live-probe the public search API (network — only runs in --live doctor)."""
        self.active_backend = None
        if _search_api_ok():
            self.active_backend = self.backends[0]
            return "ok", "B站公开搜索 API 可达（仅搜索，无凭据，curl 直连）"
        return "warn", "B站搜索 API 不可达（可能是网络问题）"

    def capability_readiness(self, status, message):
        state = "ready" if status == "ok" else "unavailable"
        backend = self.active_backend if status == "ok" else None
        return {"search": CapabilityReadiness(state, backend, message)}
