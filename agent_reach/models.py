"""Typed health models shared by doctor and integrations."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field


@dataclass(frozen=True)
class CapabilityReadiness:
    """Readiness of one upstream capability."""

    status: str
    backend: str | None = None
    detail: str = ""


@dataclass(frozen=True)
class ChannelHealth:
    """Serializable result for one platform channel."""

    status: str
    name: str
    message: str
    tier: int
    backends: list[str]
    active_backend: str | None
    capabilities: dict[str, CapabilityReadiness] = field(default_factory=dict)

    def to_dict(self) -> dict[str, object]:
        """Return a JSON/YAML-friendly representation."""

        return asdict(self)
