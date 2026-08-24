# -*- coding: utf-8 -*-
"""Validated, owner-only configuration for Agent Reach."""

import os
from pathlib import Path
from typing import Any

import yaml

from agent_reach.utils.security import atomic_write_private_text, ensure_private_directory


class Config:
    """Manages Agent Reach configuration."""

    SCHEMA_VERSION = 1
    CONFIG_DIR = Path.home() / ".agent-reach"
    CONFIG_FILE = CONFIG_DIR / "config.yaml"

    # Feature → required config keys
    FEATURE_REQUIREMENTS = {
        "twitter": ["twitter_auth_token", "twitter_ct0"],
        "groq_whisper": ["groq_api_key"],
        "openai_whisper": ["openai_api_key"],
    }

    ENVIRONMENT_KEYS = {
        "github_token": "GH_TOKEN",
        "groq_api_key": "GROQ_API_KEY",
        "openai_api_key": "OPENAI_API_KEY",
        "twitter_auth_token": "TWITTER_AUTH_TOKEN",
        "twitter_ct0": "TWITTER_CT0",
    }

    def __init__(
        self,
        config_path: Path | None = None,
        *,
        create: bool = True,
    ):
        default_path = Path.home() / ".agent-reach" / "config.yaml"
        self.config_path = Path(config_path) if config_path else default_path
        self.config_dir = self.config_path.parent
        self.create = create
        self.data: dict[str, Any] = {}
        if create:
            self._ensure_dir()
        self.load()

    def _ensure_dir(self) -> None:
        """Create config directory if it doesn't exist."""
        ensure_private_directory(self.config_dir)

    def load(self) -> None:
        """Load config from YAML file."""
        if self.config_path.exists():
            with self.config_path.open("r", encoding="utf-8") as handle:
                loaded = yaml.safe_load(handle) or {}
            if not isinstance(loaded, dict):
                raise ValueError(f"configuration must be a YAML mapping: {self.config_path}")
            self.data = {str(key): value for key, value in loaded.items()}
        else:
            self.data = {}

    def save(self) -> None:
        """Save config to YAML file."""
        if not self.create:
            raise RuntimeError("read-only Config cannot be saved")
        self._ensure_dir()
        payload = dict(self.data)
        payload.setdefault("schema_version", self.SCHEMA_VERSION)
        serialized = yaml.safe_dump(payload, default_flow_style=False, allow_unicode=True)
        atomic_write_private_text(self.config_path, serialized)
        self.data = payload

    def get(self, key: str, default: Any = None) -> Any:
        """Get a config value, then its documented environment equivalent."""
        # Config file first
        if key in self.data:
            return self.data[key]
        env_name = self.ENVIRONMENT_KEYS.get(key, key.upper())
        env_val = os.environ.get(env_name)
        if env_val:
            return env_val
        return default

    def set(self, key: str, value: Any) -> None:
        """Set a config value and save."""
        self.data[key] = value
        self.save()

    def delete(self, key: str) -> None:
        """Delete a config key and save."""
        self.data.pop(key, None)
        self.save()

    def is_configured(self, feature: str) -> bool:
        """Check if a feature has all required config."""
        required = self.FEATURE_REQUIREMENTS.get(feature)
        if not required:
            return False
        return all(self.get(k) for k in required)

    def get_configured_features(self) -> dict[str, bool]:
        """Return status of all optional features."""
        return {feature: self.is_configured(feature) for feature in self.FEATURE_REQUIREMENTS}

    def subprocess_env(self, *keys: str) -> dict[str, str]:
        """Return a child environment containing selected configured secrets."""

        env = os.environ.copy()
        for key in keys:
            value = self.get(key)
            env_name = self.ENVIRONMENT_KEYS.get(key)
            if value and env_name:
                env[env_name] = str(value)
        return env

    def to_dict(self) -> dict[str, Any]:
        """Return config as dict (masks sensitive values)."""
        masked: dict[str, Any] = {}
        for k, v in self.data.items():
            if any(
                marker in k.lower()
                for marker in ("cookie", "key", "token", "password", "proxy", "secret")
            ):
                masked[k] = f"{str(v)[:8]}..." if v else None
            else:
                masked[k] = v
        return masked
