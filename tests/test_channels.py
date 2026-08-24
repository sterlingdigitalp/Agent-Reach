"""Focused tests for request-scoped channel health adapters."""

from __future__ import annotations

import http.cookiejar
import json
from urllib.error import URLError

from agent_reach.channels import get_all_channels, get_channel
from agent_reach.channels.bilibili import BilibiliChannel
from agent_reach.channels.linkedin import LinkedInChannel
from agent_reach.channels.reddit import RedditChannel
from agent_reach.channels.v2ex import V2EXChannel
from agent_reach.channels.xiaohongshu import XiaoHongShuChannel
from agent_reach.channels.xueqiu import XueqiuChannel
from agent_reach.config import Config


class FakeResponse:
    status = 200

    def __init__(self, payload):
        self.payload = payload

    def __enter__(self):
        return self

    def __exit__(self, *_args):
        return None

    def read(self):
        if isinstance(self.payload, bytes):
            return self.payload
        return json.dumps(self.payload).encode()


def test_registry_returns_fresh_instances():
    first = get_all_channels()
    second = get_all_channels()
    assert len(first) == 13
    assert [channel.name for channel in first] == [channel.name for channel in second]
    assert all(left is not right for left, right in zip(first, second))
    assert get_channel("github").name == "github"
    assert get_channel("not-exists") is None


def test_v2ex_probe_and_exact_host(monkeypatch):
    monkeypatch.setattr(
        "urllib.request.urlopen",
        lambda *_args, **_kwargs: FakeResponse([]),
    )
    channel = V2EXChannel()
    assert channel.can_handle("https://www.v2ex.com/t/1")
    assert not channel.can_handle("https://notv2ex.com/t/1")
    status, message = channel.check()
    assert status == "ok"
    assert "公开 API" in message
    assert channel.active_backend == "V2EX API (public)"
    assert not hasattr(channel, "get_hot_topics")


def test_v2ex_probe_network_failure_is_degraded(monkeypatch):
    monkeypatch.setattr(
        "urllib.request.urlopen",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(URLError("offline")),
    )
    status, _ = V2EXChannel().check()
    assert status == "warn"


def test_xueqiu_probe_uses_supplied_config(monkeypatch, tmp_path):
    config = Config(config_path=tmp_path / "config.yaml")
    config.set("xueqiu_cookie", "xq_a_token=test; xq_is_login=1")
    captured = {}

    channel = XueqiuChannel()

    def fake_open(request, timeout=None):
        captured["cookie"] = channel._session.cookie_jar
        captured["referer"] = request.get_header("Referer")
        captured["ua"] = request.get_header("User-agent")
        return FakeResponse({"data": {"items": [{"quote": {"symbol": "SH000001"}}]}})

    monkeypatch.setattr(channel._session.opener, "open", fake_open)
    status, _ = channel.check(config)
    assert status == "ok"
    assert captured["referer"] == "https://xueqiu.com/"
    assert "Mozilla" in captured["ua"]
    assert any(cookie.name == "xq_a_token" for cookie in captured["cookie"])
    assert not hasattr(XueqiuChannel(), "get_stock_quote")


def test_xueqiu_rookiepy_failure_falls_back_to_browser_cookie3(monkeypatch):
    import sys
    import types

    import agent_reach.channels.xueqiu as module

    rookiepy = types.SimpleNamespace(
        chrome=lambda _domains: (_ for _ in ()).throw(ValueError("bad"))
    )
    cookie = http.cookiejar.Cookie(
        0,
        "xq_a_token",
        "ok",
        None,
        False,
        ".xueqiu.com",
        True,
        True,
        "/",
        True,
        True,
        None,
        True,
        None,
        None,
        {},
    )
    browser_cookie3 = types.SimpleNamespace(chrome=lambda **_kwargs: [cookie])
    monkeypatch.setitem(sys.modules, "rookiepy", rookiepy)
    monkeypatch.setitem(sys.modules, "browser_cookie3", browser_cookie3)
    assert module._XueqiuSession().load_cookies_from_browser() is True


def test_reddit_backend_selection(monkeypatch):
    channel = RedditChannel()
    monkeypatch.setattr(channel, "_check_opencli", lambda: ("warn", "not ready"))
    monkeypatch.setattr(channel, "_check_rdt", lambda: ("ok", "rdt ready"))
    status, _ = channel.check()
    assert status == "ok"
    assert channel.active_backend == "rdt-cli"


def test_reddit_no_backend_is_off(monkeypatch):
    channel = RedditChannel()
    monkeypatch.setattr(channel, "_check_opencli", lambda: None)
    monkeypatch.setattr(channel, "_check_rdt", lambda: None)
    status, _ = channel.check()
    assert status == "off"
    assert channel.active_backend is None


def test_xhs_backend_selection(monkeypatch):
    channel = XiaoHongShuChannel()
    monkeypatch.setattr(channel, "_check_opencli", lambda: None)
    monkeypatch.setattr(channel, "_check_mcp", lambda: ("ok", "mcp ready"))
    monkeypatch.setattr(channel, "_check_xhs_cli", lambda: ("warn", "legacy"))
    status, _ = channel.check()
    assert status == "ok"
    assert channel.active_backend == "xiaohongshu-mcp"


def test_xhs_no_backend_is_off(monkeypatch):
    channel = XiaoHongShuChannel()
    monkeypatch.setattr(channel, "_check_opencli", lambda: None)
    monkeypatch.setattr(channel, "_check_mcp", lambda: None)
    monkeypatch.setattr(channel, "_check_xhs_cli", lambda: None)
    status, _ = channel.check()
    assert status == "off"


def test_bilibili_limited_api_is_degraded(monkeypatch):
    channel = BilibiliChannel()
    monkeypatch.setattr(channel, "_check_bili_cli", lambda: None)
    monkeypatch.setattr(channel, "_check_opencli", lambda: None)
    monkeypatch.setattr(channel, "_check_search_api", lambda: ("warn", "search only"))
    status, _ = channel.check()
    assert status == "warn"
    assert channel.active_backend == "B站搜索 API"


def test_bilibili_healthy_cli_wins(monkeypatch):
    channel = BilibiliChannel()
    monkeypatch.setattr(channel, "_check_bili_cli", lambda: ("ok", "full"))
    monkeypatch.setattr(channel, "_check_opencli", lambda: ("warn", "not ready"))
    monkeypatch.setattr(channel, "_check_search_api", lambda: ("warn", "search only"))
    status, _ = channel.check()
    assert status == "ok"
    assert channel.active_backend == "bili-cli"


def test_linkedin_mcp_requires_config_and_live_service(monkeypatch):
    monkeypatch.setattr(
        "agent_reach.channels.linkedin.probe_command",
        lambda *_args, **_kwargs: type(
            "Probe",
            (),
            {"status": "ok", "ok": True, "output": "linkedin http://localhost:8001/mcp"},
        )(),
    )
    monkeypatch.setattr("agent_reach.channels.linkedin._mcp_service_reachable", lambda: True)
    channel = LinkedInChannel()
    status, _ = channel.check()
    assert status == "ok"
    assert channel.active_backend == "linkedin-scraper-mcp"
    assert channel.capability_readiness(status, "")["job_search"].status == "ready"


def test_linkedin_jina_fallback_is_read_only_degraded(monkeypatch):
    monkeypatch.setattr(
        "agent_reach.channels.linkedin.probe_command",
        lambda *_args, **_kwargs: type(
            "Probe",
            (),
            {"status": "missing", "ok": False, "output": ""},
        )(),
    )
    monkeypatch.setattr("agent_reach.channels.linkedin._mcp_service_reachable", lambda: False)
    channel = LinkedInChannel()
    status, _ = channel.check()
    capabilities = channel.capability_readiness(status, "fallback")
    assert status == "warn"
    assert channel.active_backend == "Jina Reader"
    assert capabilities["read"].status == "degraded"
    assert capabilities["job_search"].status == "unavailable"


def test_github_config_token_reaches_probe_environment(monkeypatch, tmp_path):
    from agent_reach.channels.github import GitHubChannel

    config = Config(config_path=tmp_path / "config.yaml")
    config.set("github_token", "test-token")
    captured = {}

    def fake_probe(*_args, **kwargs):
        captured["env"] = kwargs["env"]
        return type("Probe", (), {"status": "ok", "ok": True})()

    monkeypatch.setattr("agent_reach.channels.github.probe_command", fake_probe)
    status, _ = GitHubChannel().check(config)
    assert status == "ok"
    assert captured["env"]["GH_TOKEN"] == "test-token"


def test_exa_broken_mcporter_reports_error(monkeypatch):
    from agent_reach.channels.exa_search import ExaSearchChannel

    monkeypatch.setattr(
        "agent_reach.channels.exa_search.probe_command",
        lambda *_args, **_kwargs: type(
            "Probe",
            (),
            {"status": "broken", "ok": False, "hint": "", "output": ""},
        )(),
    )
    status, message = ExaSearchChannel().check()
    assert status == "error"
    assert "mcporter@VERSION" in message


def test_exa_requires_a_successful_live_read_only_query(monkeypatch):
    from agent_reach.channels.exa_search import ExaSearchChannel
    from agent_reach.probe import ProbeResult

    calls = []

    def fake_probe(_cmd, args, **_kwargs):
        calls.append(args)
        if args == ["config", "list"]:
            return ProbeResult("ok", output="exa https://mcp.exa.ai/mcp")
        return ProbeResult("error", output="upstream unavailable")

    monkeypatch.setattr("agent_reach.channels.exa_search.probe_command", fake_probe)
    status, message = ExaSearchChannel().check()
    assert status == "warn"
    assert "真实只读查询失败" in message
    assert calls[1][0] == "call"
    assert "web_search_exa" in calls[1][1]


def test_xiaoyuzhou_ffmpeg_broken(monkeypatch):
    from agent_reach.channels.xiaoyuzhou import XiaoyuzhouChannel

    monkeypatch.setattr(
        "agent_reach.channels.xiaoyuzhou.probe_command",
        lambda *_args, **_kwargs: type("Probe", (), {"status": "broken", "ok": False})(),
    )
    status, _ = XiaoyuzhouChannel().check()
    assert status == "error"


def test_exact_host_checks_reject_lookalikes():
    samples = {
        "github": ("https://github.com/a/b", "https://notgithub.com/a/b"),
        "twitter": ("https://x.com/a/status/1", "https://notx.com/a/status/1"),
        "youtube": ("https://youtube.com/watch?v=1", "https://evilyoutube.com/watch?v=1"),
        "reddit": ("https://reddit.com/r/python", "https://fakereddit.com/r/python"),
        "linkedin": ("https://linkedin.com/in/a", "https://linkedin.com.evil.test/in/a"),
    }
    for name, (good, bad) in samples.items():
        channel = get_channel(name)
        assert channel.can_handle(good)
        assert not channel.can_handle(bad)
