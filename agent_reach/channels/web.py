# -*- coding: utf-8 -*-
"""Web — any HTTP(S) URL via Jina Reader."""

import urllib.request

from .base import Channel

_UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"


class WebChannel(Channel):
    name = "web"
    description = "任意网页"
    backends = ["Jina Reader"]
    tier = 0

    def can_handle(self, url: str) -> bool:
        return url.startswith(("http://", "https://"))

    def check(self, config=None):
        request = urllib.request.Request(
            "https://r.jina.ai/https://example.com",
            headers={"User-Agent": _UA, "Range": "bytes=0-0"},
        )
        try:
            with urllib.request.urlopen(request, timeout=5) as response:
                if response.status >= 400:
                    raise OSError(f"HTTP {response.status}")
        except Exception as exc:
            self.active_backend = None
            return "warn", f"Jina Reader 网络探测失败：{exc}"
        self.active_backend = self.backends[0]
        return "ok", "Jina Reader 网络探测成功（只读）"
