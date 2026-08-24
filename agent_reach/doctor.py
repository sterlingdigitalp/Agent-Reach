# -*- coding: utf-8 -*-
"""Read-only, bounded environment health checks."""

from __future__ import annotations

import contextvars
from concurrent.futures import ThreadPoolExecutor, as_completed
from html import escape as html_escape
from pathlib import Path
from typing import Any, Callable

from agent_reach.channels import get_all_channels
from agent_reach.config import Config
from agent_reach.models import CapabilityReadiness, ChannelHealth
from agent_reach.probe import probe_session


def check_all(config: Config | None, *, deadline: float = 30.0) -> dict[str, dict[str, object]]:
    """Check all channels and return status dict.

    A single misbehaving channel must never take the whole report down,
    so per-channel exceptions degrade to status="error".
    """
    channels = get_all_channels()

    def check_channel(ch):
        try:
            status, message = ch.check(config)
            active = getattr(ch, "active_backend", None)
        except Exception as exc:  # doctor must survive any channel
            # Clear request-local backend state before reporting an error.
            status, message, active = "error", f"体检异常：{exc}", None
            ch.active_backend = None
        if hasattr(ch, "capability_readiness"):
            capabilities = ch.capability_readiness(status, message)
        else:
            translated = {
                "ok": "ready",
                "warn": "degraded",
                "off": "unavailable",
                "error": "error",
            }.get(status, "error")
            capabilities = {"read": CapabilityReadiness(translated, active, message)}
        return ch.name, ChannelHealth(
            status=status,
            name=ch.description,
            message=message,
            tier=ch.tier,
            backends=list(ch.backends),
            active_backend=active,
            capabilities=capabilities,
        ).to_dict()

    results: dict[str, dict[str, object]] = {}
    executor = ThreadPoolExecutor(max_workers=min(8, len(channels)))
    with probe_session():
        futures = {
            executor.submit(contextvars.copy_context().run, check_channel, channel): channel
            for channel in channels
        }
        try:
            for future in as_completed(futures, timeout=deadline):
                name, result = future.result()
                results[name] = result
        except TimeoutError:
            pass
        finally:
            executor.shutdown(wait=False, cancel_futures=True)

    for channel in channels:
        if channel.name not in results:
            channel.active_backend = None
            message = f"健康检查超过总时限（{deadline:g}s）"
            results[channel.name] = ChannelHealth(
                status="error",
                name=channel.description,
                message=message,
                tier=channel.tier,
                backends=list(channel.backends),
                active_backend=None,
                capabilities=channel.capability_readiness("error", message),
            ).to_dict()

    # Preserve registry order despite concurrent completion.
    results = {channel.name: results[channel.name] for channel in channels}
    return results


def _name_msg(r: dict[str, object], escape: Callable[[str], str]) -> str:
    """Render one channel line; show the active backend when there is a choice."""
    text = f"[bold]{escape(str(r['name']))}[/bold] — {escape(str(r['message']))}"
    active = r.get("active_backend")
    backends = r.get("backends", [])
    if active and isinstance(backends, list) and len(backends) > 1:
        text += f" [dim]（当前后端：{escape(str(active))}）[/dim]"
    return text


def format_report(results: dict[str, dict[str, object]]) -> str:
    """Format results as a readable text report (with Rich markup)."""
    rich_escape: Any = None
    try:
        from rich.markup import escape as imported_rich_escape

        rich_escape = imported_rich_escape
    except ImportError:
        pass

    def escape(value: str) -> str:
        return rich_escape(value) if rich_escape is not None else html_escape(value)

    lines = []
    lines.append("[bold cyan]Agent Reach 状态[/bold cyan]")
    lines.append("[cyan]" + "=" * 40 + "[/cyan]")
    lines.append(
        "图例：[green]✅[/green] 可用  [yellow][!][/yellow] 已装但需配置/登录  [red][X][/red] 未安装"
    )

    ok_count = sum(1 for r in results.values() if r["status"] == "ok")
    total = len(results)

    # Tier 0 — zero config
    lines.append("")
    lines.append("[bold]✅ 装好即用：[/bold]")
    for key, r in results.items():
        if r["tier"] == 0:
            name_msg = _name_msg(r, escape)
            if r["status"] == "ok":
                lines.append(f"  [green]✅[/green] {name_msg}")
            elif r["status"] == "warn":
                lines.append(f"  [yellow][!][/yellow]  {name_msg}")
            elif r["status"] in ("off", "error"):
                lines.append(f"  [red][X][/red]  {name_msg}")

    # Tier 1 — needs free key / login
    tier1 = {k: r for k, r in results.items() if r["tier"] == 1}
    tier1_active = {k: r for k, r in tier1.items() if r["status"] == "ok"}
    tier1_inactive = {k: r for k, r in tier1.items() if r["status"] != "ok"}
    if tier1_active:
        lines.append("")
        lines.append("[bold]可选渠道（已安装）：[/bold]")
        for key, r in tier1_active.items():
            lines.append(f"  [green]✅[/green] {_name_msg(r, escape)}")

    # Tier 2 — optional complex setup
    tier2 = {k: r for k, r in results.items() if r["tier"] == 2}
    tier2_active = {k: r for k, r in tier2.items() if r["status"] == "ok"}
    tier2_inactive = {k: r for k, r in tier2.items() if r["status"] != "ok"}
    if tier2_active:
        if not tier1_active:
            lines.append("")
            lines.append("[bold]可选渠道（已安装）：[/bold]")
        for key, r in tier2_active.items():
            lines.append(f"  [green]✅[/green] {_name_msg(r, escape)}")

    lines.append("")
    status_color = "green" if ok_count == total else ("yellow" if ok_count > 0 else "red")
    lines.append(f"状态：[{status_color}]{ok_count}/{total}[/{status_color}] 个渠道可用")

    # Summarize inactive optional channels in one line instead of listing each
    all_inactive = list(tier1_inactive.values()) + list(tier2_inactive.values())
    if all_inactive:
        names = [str(r["name"]) for r in all_inactive]
        lines.append(
            f"还有 {len(names)} 个可选渠道可以解锁（{'、'.join(names)}），"
            "先审阅 `agent-reach install --channels=... --dry-run`，"
            "再通过单独的明确授权执行安装。"
        )

    # Security check: config file permissions (Unix only)
    import stat
    import sys

    config_path = Path.home() / ".agent-reach" / "config.yaml"
    if config_path.exists() and sys.platform != "win32":
        try:
            mode = config_path.stat().st_mode
            if mode & (stat.S_IRGRP | stat.S_IROTH):
                lines.append("")
                lines.append(
                    "[bold red][!]  安全提示：config.yaml 权限过宽（其他用户可读）[/bold red]"
                )
                lines.append("   修复：chmod 600 ~/.agent-reach/config.yaml")
        except OSError:
            pass

    return "\n".join(lines)
