"""Hermetic defaults for the entire test suite."""

from __future__ import annotations

import socket

import pytest


@pytest.fixture(autouse=True)
def isolated_user_state(tmp_path, monkeypatch):
    """Keep tests away from the developer's home, browsers, and network."""

    home = tmp_path / "home"
    monkeypatch.setenv("HOME", str(home))
    monkeypatch.setenv("XDG_CONFIG_HOME", str(home / ".config"))
    monkeypatch.setenv("AGENT_REACH_TESTING", "1")
    monkeypatch.delenv("OPENCLAW_HOME", raising=False)

    def deny_network(*_args, **_kwargs):
        raise OSError("network disabled by hermetic test fixture")

    monkeypatch.setattr(socket, "create_connection", deny_network)
