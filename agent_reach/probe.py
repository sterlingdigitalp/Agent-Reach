# -*- coding: utf-8 -*-
"""Lightweight upstream command probing.

Distinguishes the three failure modes that look identical to shutil.which():
  - missing: command not on PATH
  - broken: command exists but cannot execute — most commonly a stale venv
    shebang after a system Python upgrade (pipx/uv tool installs break this
    way: which() finds the shim, but exec fails with FileNotFoundError
    pointing at the shim itself)
  - timeout/error: command runs but misbehaves

Channels use probe_command() inside check() so doctor reports real health,
not just file existence.
"""

import shutil
import subprocess
from collections.abc import Iterator, Mapping
from concurrent.futures import Future
from contextlib import contextmanager
from contextvars import ContextVar
from dataclasses import dataclass, field
from threading import Lock
from typing import Sequence

from agent_reach.utils.process import utf8_subprocess_env

#: Exit codes shells use for "found but not executable" / "not found".
_BROKEN_EXIT_CODES = (126, 127)
_ProbeKey = tuple[object, ...]


@dataclass
class _ProbeSessionCache:
    """Thread-safe single-flight cache shared by one doctor request."""

    lock: Lock = field(default_factory=Lock)
    results: dict[_ProbeKey, Future["ProbeResult"]] = field(default_factory=dict)


_PROBE_CACHE: ContextVar[_ProbeSessionCache | None] = ContextVar(
    "agent_reach_probe_cache",
    default=None,
)


@dataclass
class ProbeResult:
    status: str  # "ok" | "missing" | "broken" | "timeout" | "error"
    output: str = ""
    hint: str = ""

    @property
    def ok(self) -> bool:
        return self.status == "ok"


def reinstall_hint(package: str) -> str:
    """Prescription for a broken (stale-venv) CLI install."""
    return (
        f"命令存在但无法执行——通常是系统 Python 升级后 venv 解释器丢失。重装即可修复：\n"
        f"  uv tool install --force {package}\n"
        f"或：pipx reinstall {package}"
    )


def probe_command(
    cmd: str,
    args: Sequence[str] = ("--version",),
    timeout: int = 10,
    retries: int = 0,
    package: str | None = None,
    env: Mapping[str, str] | None = None,
) -> ProbeResult:
    """Actually execute `cmd *args` and classify the result.

    Intended for SIDE-EFFECT-FREE health probes only (version/status
    commands): retries re-run the command verbatim with no backoff, so a
    non-idempotent command would repeat its effect.

    package: pip/pipx package name used in the broken-install hint
             (defaults to cmd).
    """
    path = shutil.which(cmd)
    if not path:
        return ProbeResult("missing")

    cache = _PROBE_CACHE.get()
    key = (path, tuple(args), timeout, retries, package, id(env) if env is not None else None)
    future: Future[ProbeResult] | None = None
    owns_probe = True
    if cache is not None:
        with cache.lock:
            future = cache.results.get(key)
            if future is None:
                future = Future()
                cache.results[key] = future
            else:
                owns_probe = False
        if not owns_probe:
            return future.result()

    try:
        last = ProbeResult("error", hint="probe did not run")
        for _ in range(retries + 1):
            last = _run_once(path, args, timeout, package or cmd, env)
            if last.ok:
                break
            # missing/broken won't heal between retries — only transient
            # failures (timeout/error) are worth a second attempt
            if last.status in ("missing", "broken"):
                break
        if future is not None:
            future.set_result(last)
        return last
    except BaseException as exc:
        if future is not None:
            future.set_exception(exc)
        raise


def _run_once(
    path: str,
    args: Sequence[str],
    timeout: int,
    package: str,
    env: Mapping[str, str] | None,
) -> ProbeResult:
    try:
        r = subprocess.run(
            [path, *args],
            capture_output=True,
            encoding="utf-8",
            errors="replace",
            timeout=timeout,
            env=utf8_subprocess_env(env),
        )
    except FileNotFoundError:
        # which() found it but exec failed: the shebang interpreter is gone
        return ProbeResult("broken", hint=reinstall_hint(package))
    except OSError:
        return ProbeResult("broken", hint=reinstall_hint(package))
    except subprocess.TimeoutExpired:
        return ProbeResult("timeout", hint=f"`{path}` 响应超时（>{timeout}s）")

    if r.returncode in _BROKEN_EXIT_CODES:
        return ProbeResult("broken", hint=reinstall_hint(package))

    output = (r.stdout or "") + (r.stderr or "")
    if r.returncode != 0:
        return ProbeResult("error", output=output.strip())
    return ProbeResult("ok", output=output.strip())


@contextmanager
def probe_session() -> Iterator[None]:
    """Cache identical side-effect-free probes for one doctor request."""

    token = _PROBE_CACHE.set(_ProbeSessionCache())
    try:
        yield
    finally:
        _PROBE_CACHE.reset(token)
