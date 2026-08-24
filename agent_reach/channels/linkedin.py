# -*- coding: utf-8 -*-
"""LinkedIn — MCP for structured search, Jina for read-only fallback."""

import urllib.error
import urllib.request

from agent_reach.models import CapabilityReadiness
from agent_reach.probe import probe_command
from agent_reach.utils.urls import host_matches

from .base import Channel

#: mcporter 是 npm 包，断链处方与默认的 pipx/uv 不同
_MCPORTER_BROKEN_HINT = "mcporter 无法执行（node 环境损坏）；请审阅并重装固定的 mcporter@VERSION"
_MCP_ENDPOINT = "http://localhost:8001/mcp"


def _mcp_service_reachable(timeout: int = 3) -> bool:
    request = urllib.request.Request(_MCP_ENDPOINT, method="GET")
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
    try:
        opener.open(request, timeout=timeout)
        return True
    except urllib.error.HTTPError:
        return True
    except OSError:
        return False


class LinkedInChannel(Channel):
    name = "linkedin"
    description = "LinkedIn 职业社交"
    backends = ["linkedin-scraper-mcp", "Jina Reader"]
    tier = 2
    network = True  # probe makes an outbound request
    capabilities = ("read", "profile", "job_search")

    def can_handle(self, url: str) -> bool:
        return host_matches(url, "linkedin.com")

    def check(self, config=None):
        self.active_backend = None
        probe = probe_command("mcporter", ["config", "list"], timeout=10, package="mcporter")
        mcp_running = _mcp_service_reachable()
        if probe.status == "missing":
            self.active_backend = "Jina Reader"
            return "warn", (
                "公开页面可通过 Jina Reader 只读访问。结构化功能需要：\n"
                "  pip install linkedin-scraper-mcp\n"
                f"  mcporter config add linkedin {_MCP_ENDPOINT}\n"
                "  详见 https://github.com/stickerdaniel/linkedin-mcp-server"
            )
        if probe.status == "broken":
            return "error", _MCPORTER_BROKEN_HINT
        if not probe.ok:  # timeout / error
            return "error", f"mcporter 执行异常：{probe.hint or probe.output or probe.status}"
        if "linkedin" in probe.output.lower() and mcp_running:
            self.active_backend = "linkedin-scraper-mcp"
            return "ok", "完整可用（Profile、公司、职位搜索）"
        self.active_backend = "Jina Reader"
        return "warn", (
            "公开页面可通过 Jina Reader 只读访问；LinkedIn MCP 未配置或服务未运行：\n"
            "  pip install linkedin-scraper-mcp\n"
            f"  mcporter config add linkedin {_MCP_ENDPOINT}"
        )

    def capability_readiness(self, status, message):
        if self.active_backend == "linkedin-scraper-mcp" and status == "ok":
            return super().capability_readiness(status, message)
        return {
            "read": CapabilityReadiness("degraded", "Jina Reader", message),
            "profile": CapabilityReadiness("unavailable", None, message),
            "job_search": CapabilityReadiness("unavailable", None, message),
        }
