# -*- coding: utf-8 -*-
"""Agent Reach — Give your AI Agent eyes to see the entire internet."""

from typing import TYPE_CHECKING, Any

from agent_reach._version import __version__

__author__ = "Neo Reid"

if TYPE_CHECKING:
    from agent_reach.core import AgentReach


def __getattr__(name: str) -> Any:
    """Keep package metadata importable without eagerly loading runtime deps."""

    if name == "AgentReach":
        from agent_reach.core import AgentReach

        return AgentReach
    raise AttributeError(name)


__all__ = ["AgentReach", "__author__", "__version__"]
