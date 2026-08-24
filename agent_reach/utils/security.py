"""Security-sensitive filesystem helpers."""

from __future__ import annotations

import os
import stat
import tempfile
from pathlib import Path

OWNER_FILE_MODE = stat.S_IRUSR | stat.S_IWUSR
OWNER_DIR_MODE = stat.S_IRWXU


def ensure_private_directory(path: str | Path) -> Path:
    """Create *path* and ensure it is accessible only by its owner on POSIX."""

    target = Path(path)
    target.mkdir(parents=True, exist_ok=True, mode=OWNER_DIR_MODE)
    if os.name != "nt":
        target.chmod(OWNER_DIR_MODE)
    return target


def atomic_write_private_text(
    path: str | Path,
    content: str,
    *,
    encoding: str = "utf-8",
) -> None:
    """Atomically replace *path* with an owner-only text file.

    Replacing rather than truncating is important: the mode supplied to
    ``os.open(..., O_CREAT, 0o600)`` does not repair an existing 0644 file.
    The temporary file is created in the destination directory, fsynced, then
    moved into place with ``os.replace``.
    """

    target = Path(path)
    ensure_private_directory(target.parent)
    fd, temporary_name = tempfile.mkstemp(prefix=f".{target.name}.", dir=target.parent)
    temporary = Path(temporary_name)
    try:
        if os.name != "nt":
            os.fchmod(fd, OWNER_FILE_MODE)
        with os.fdopen(fd, "w", encoding=encoding) as handle:
            handle.write(content)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, target)
        if os.name != "nt":
            target.chmod(OWNER_FILE_MODE)
    except BaseException:
        try:
            os.close(fd)
        except OSError:
            pass
        try:
            temporary.unlink()
        except OSError:
            pass
        raise
