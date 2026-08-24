# -*- coding: utf-8 -*-
"""V2EX public API capability probe."""

import json
import urllib.request
from typing import Any

from agent_reach.models import CapabilityReadiness
from agent_reach.utils.urls import host_matches

from .base import Channel

_UA = "agent-reach/1.0"
_TIMEOUT = 10


def _get_json(url: str) -> Any:
    """Fetch *url* and return parsed JSON. Raises on HTTP/network errors."""
    req = urllib.request.Request(url, headers={"User-Agent": _UA})
    with urllib.request.urlopen(req, timeout=_TIMEOUT) as resp:
        return json.loads(resp.read().decode("utf-8"))


class V2EXChannel(Channel):
    name = "v2ex"
    description = "V2EX 节点、主题与回复"
    backends = ["V2EX API (public)"]
    tier = 0
    network = True  # probe makes an outbound request
    capabilities = ("read", "search")

    # ------------------------------------------------------------------ #
    # URL routing
    # ------------------------------------------------------------------ #

    def can_handle(self, url: str) -> bool:
        return host_matches(url, "v2ex.com")

    # ------------------------------------------------------------------ #
    # Health check
    # ------------------------------------------------------------------ #

    def check(self, config=None):
        try:
            _get_json("https://www.v2ex.com/api/topics/show.json?node_name=python&page=1")
            self.active_backend = self.backends[0]
            return "ok", "公开 API 可用（热门主题、节点浏览、主题详情、用户信息）"
        except Exception as e:
            self.active_backend = None
            return "warn", f"V2EX API 连接失败（可能需要代理）：{e}"

    def capability_readiness(self, status, message):
        readiness = super().capability_readiness(status, message)
        readiness["search"] = CapabilityReadiness(
            "unavailable",
            None,
            "V2EX public API has no full-text search; use Exa with site:v2ex.com",
        )
        return readiness
