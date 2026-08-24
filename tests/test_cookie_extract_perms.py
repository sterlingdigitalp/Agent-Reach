# -*- coding: utf-8 -*-
"""Credential storage after browser cookie extraction is owner-only (0o600).

Agent Reach persists Twitter tokens (and the Xueqiu cookie string) into
``~/.agent-reach/config.yaml`` and nowhere else — the legacy xfetch/bird
side-channel writers were removed so config.yaml is the single source of
truth. This test verifies that the file cookie extraction writes through
lands with restricted permissions, starting even from an insecure 0644 file.

Companion to tests/test_config.py::test_save_creates_file_with_restricted_permissions.
"""

import os
import stat
import sys

import pytest

from agent_reach.config import Config


def _owner_only(path: str) -> bool:
    mode = os.stat(path).st_mode
    return not (mode & (stat.S_IRGRP | stat.S_IWGRP | stat.S_IROTH | stat.S_IWOTH))


@pytest.mark.skipif(sys.platform == "win32", reason="POSIX perm semantics only")
def test_configure_from_browser_persists_tokens_0600(tmp_path, monkeypatch):
    """A successful Twitter extraction stores tokens in a 0600 config.yaml."""
    monkeypatch.setenv("HOME", str(tmp_path))
    cfg_path = tmp_path / ".agent-reach" / "config.yaml"
    config = Config(config_path=cfg_path)

    import agent_reach.cookie_extract as ce

    monkeypatch.setattr(
        ce, "extract_all", lambda browser: {"twitter": {"auth_token": "auth_xxx", "ct0": "ct0_yyy"}}
    )

    results = ce.configure_from_browser("chrome", config)

    assert any(name == "Twitter/X" and ok for name, ok, _ in results)
    assert cfg_path.exists()
    assert _owner_only(str(cfg_path)), "config.yaml holding tokens must be owner-only"

    reloaded = Config(config_path=cfg_path)
    assert reloaded.get("twitter_auth_token") == "auth_xxx"
    assert reloaded.get("twitter_ct0") == "ct0_yyy"


@pytest.mark.skipif(sys.platform == "win32", reason="POSIX perm semantics only")
def test_config_save_repairs_legacy_0644(tmp_path, monkeypatch):
    """An existing world-readable config is tightened to 0600 on the next save."""
    monkeypatch.setenv("HOME", str(tmp_path))
    cfg_dir = tmp_path / ".agent-reach"
    cfg_dir.mkdir(parents=True)
    cfg_path = cfg_dir / "config.yaml"
    cfg_path.write_text("schema_version: 1\n", encoding="utf-8")
    os.chmod(cfg_path, 0o644)

    config = Config(config_path=cfg_path)
    config.set("twitter_auth_token", "new-auth")

    assert _owner_only(str(cfg_path))
