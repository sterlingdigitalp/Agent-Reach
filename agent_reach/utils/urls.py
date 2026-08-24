"""URL ownership helpers that reject lookalike domains."""

from __future__ import annotations

from urllib.parse import urlparse


def hostname(url: str) -> str:
    """Return a normalized hostname, or an empty string for malformed URLs."""

    value = url if "://" in url else f"https://{url}"
    try:
        return (urlparse(value).hostname or "").rstrip(".").lower()
    except ValueError:
        return ""


def host_matches(url: str, *domains: str) -> bool:
    """Return whether *url* belongs to an exact domain or one of its subdomains."""

    host = hostname(url)
    return any(host == domain or host.endswith(f".{domain}") for domain in domains)
