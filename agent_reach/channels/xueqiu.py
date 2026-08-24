# -*- coding: utf-8 -*-
"""Xueqiu (雪球) — stock quotes, search, trending posts & hot stocks."""

import http.cookiejar
import json
import urllib.request
from typing import Any

from agent_reach.utils.urls import host_matches

from .base import Channel

_UA = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/120.0.0.0 Safari/537.36"
)
_REFERER = "https://xueqiu.com/"
_TIMEOUT = 10
_XUEQIU_HOME = "https://xueqiu.com"

# --------------- cookie-aware HTTP session --------------- #


class _XueqiuSession:
    """Request-scoped cookie jar + opener.

    One instance per channel instance (and channels are created fresh per
    request via ``get_all_channels()``), so cookie state is never shared
    across doctor threads or MCP requests — module-global mutable state
    here previously raced under ``doctor.py``'s thread pool.
    """

    def __init__(self) -> None:
        self.cookie_jar = http.cookiejar.CookieJar()
        self.opener = urllib.request.build_opener(
            urllib.request.HTTPCookieProcessor(self.cookie_jar),
        )
        self.initialized = False

    def inject_cookie_string(self, cookie_str: str) -> None:
        """Parse a 'name=value; name2=value2' string and inject into the jar."""
        for pair in cookie_str.split(";"):
            pair = pair.strip()
            if "=" not in pair:
                continue
            name, _, value = pair.partition("=")
            cookie = http.cookiejar.Cookie(
                version=0,
                name=name.strip(),
                value=value.strip(),
                port=None,
                port_specified=False,
                domain=".xueqiu.com",
                domain_specified=True,
                domain_initial_dot=True,
                path="/",
                path_specified=True,
                secure=True,
                expires=None,
                discard=True,
                comment=None,
                comment_url=None,
                rest={},
            )
            self.cookie_jar.set_cookie(cookie)

    def load_cookies_from_config(self, config=None) -> bool:
        """Try to load Xueqiu cookies from agent-reach config (xueqiu_cookie key)."""
        try:
            if config is None:
                from ..config import Config

                config = Config(create=False)
            cookie_str = config.get("xueqiu_cookie")
            if not cookie_str:
                return False
            self.inject_cookie_string(cookie_str)
            return True
        except Exception:
            return False

    def load_cookies_from_browser(self) -> bool:
        """Try to silently load Xueqiu cookies from the local Chrome browser.

        Only succeeds when rookiepy/browser_cookie3 is installed AND the user
        is logged in (xq_a_token present). Failures are silently ignored so
        that agents without a local browser keep working.
        """
        try:
            try:
                import rookiepy

                cookies = rookiepy.chrome([".xueqiu.com"])
                if not any(c.get("name") == "xq_a_token" for c in cookies):
                    return False
                for c in cookies:
                    self.inject_cookie_string(f"{c['name']}={c['value']}")
                return True
            except Exception:
                import browser_cookie3

                cookies = list(browser_cookie3.chrome(domain_name=".xueqiu.com"))
                if not any(c.name == "xq_a_token" for c in cookies):
                    return False
                for c in cookies:
                    self.cookie_jar.set_cookie(c)
                return True
        except Exception:
            return False

    def ensure_cookies(self, config=None) -> None:
        """Populate session cookies using the best available source.

        Priority order:
        1. Saved cookie string in ~/.agent-reach/config.yaml
           (set by configure --from-browser)
        2. Live Chrome browser cookies via rookiepy/browser_cookie3
           (if installed + logged in)
        3. Homepage visit fallback (only yields anti-DDoS acw_tc,
           not enough for stock APIs)
        """
        if self.initialized:
            return
        if self.load_cookies_from_config(config):
            self.initialized = True
            return
        if self.load_cookies_from_browser():
            self.initialized = True
            return
        # Fallback: visit homepage to pick up acw_tc anti-DDoS cookie.
        req = urllib.request.Request(_XUEQIU_HOME, headers={"User-Agent": _UA})
        self.opener.open(req, timeout=_TIMEOUT)
        self.initialized = True

    def get_json(self, url: str, config=None) -> Any:
        """Fetch *url* with Xueqiu session cookies and return parsed JSON."""
        self.ensure_cookies(config)
        req = urllib.request.Request(url, headers={"User-Agent": _UA, "Referer": _REFERER})
        with self.opener.open(req, timeout=_TIMEOUT) as resp:
            return json.loads(resp.read().decode("utf-8"))


class XueqiuChannel(Channel):
    name = "xueqiu"
    description = "雪球股票行情与社区动态"
    backends = ["Xueqiu API (需要登录 Cookie)"]
    tier = 1
    capabilities = ("quotes", "search", "read")

    def __init__(self) -> None:
        super().__init__()
        self._session = _XueqiuSession()

    # ------------------------------------------------------------------ #
    # URL routing
    # ------------------------------------------------------------------ #

    def can_handle(self, url: str) -> bool:
        return host_matches(url, "xueqiu.com")

    # ------------------------------------------------------------------ #
    # Health check
    # ------------------------------------------------------------------ #

    def check(self, config=None):
        self.active_backend = None
        try:
            data = self._session.get_json(
                "https://stock.xueqiu.com/v5/stock/batch/quote.json?symbol=SH000001",
                config,
            )
            items = (data.get("data") or {}).get("items") or []
            if items:
                self.active_backend = self.backends[0]
                return "ok", "公开 API 可用（行情、搜索、热帖、热股）"
            return "warn", "API 响应异常（返回数据为空）"
        except Exception as e:
            return "warn", (
                f"Xueqiu API 连接失败：{e}。"
                "请先登录雪球后运行：agent-reach configure --from-browser chrome"
            )
