#!/usr/bin/env python3
"""Fail when tracked or untracked source contains common live credential formats."""

from __future__ import annotations

import re
import subprocess
from pathlib import Path

PATTERNS = {
    "private key": re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"),
    "GitHub token": re.compile(r"\b(?:ghp|github_pat)_[A-Za-z0-9_]{20,}\b"),
    "AWS access key": re.compile(r"\bAKIA[0-9A-Z]{16}\b"),
    "OpenAI key": re.compile(r"\bsk-[A-Za-z0-9]{32,}\b"),
    "Groq key": re.compile(r"\bgsk_[A-Za-z0-9]{32,}\b"),
}


def main() -> int:
    candidates = subprocess.run(
        ["git", "ls-files", "--cached", "--others", "--exclude-standard", "-z"],
        check=True,
        capture_output=True,
    ).stdout.split(b"\0")
    findings: list[str] = []
    for raw_path in candidates:
        if not raw_path:
            continue
        path = Path(raw_path.decode())
        try:
            text = path.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            continue
        for label, pattern in PATTERNS.items():
            if pattern.search(text):
                findings.append(f"{path}: possible {label}")
    if findings:
        print("\n".join(findings))
        return 1
    print("No credential-shaped values found in repository text files.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
