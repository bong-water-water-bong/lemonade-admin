"""Local backup primitives for the internal admin package.

Backups are owner/admin operations. This module intentionally uses only the
stdlib so a cash-only offline store can create rollback snapshots without cloud
services or additional runtime dependencies.
"""

from __future__ import annotations

import hashlib
import json
import tarfile
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path


class BackupError(ValueError):
    """Raised when a local backup cannot be created or read safely."""


@dataclass(frozen=True)
class BackupRecord:
    """Metadata for a local backup archive."""

    label: str
    path: Path
    sha256: str
    created_at: str


def create_backup(*, paths: tuple[Path, ...], out_dir: Path, label: str) -> BackupRecord:
    """Create a gzipped tar backup of selected local paths.

    Returns a metadata record and writes a sibling ``.json`` metadata file.
    """
    if not paths:
        raise BackupError("at least one path is required")
    for path in paths:
        if not path.exists():
            raise BackupError(f"backup path {path} does not exist")
    out_dir.mkdir(parents=True, exist_ok=True)
    created_at = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
    safe_label = _safe_label(label)
    archive = out_dir / f"{created_at}-{safe_label}.tar.gz"

    with tarfile.open(archive, "w:gz") as tar:
        for path in paths:
            tar.add(path, arcname=path.name, recursive=True)

    digest = _sha256(archive)
    record = BackupRecord(label=label, path=archive, sha256=digest, created_at=created_at)
    _write_record(record)
    return record


def list_backups(out_dir: Path) -> tuple[BackupRecord, ...]:
    """List backup metadata records newest-first by archive filename."""
    if not out_dir.exists():
        return ()
    records: list[BackupRecord] = []
    for meta in sorted(out_dir.glob("*.tar.gz.json"), reverse=True):
        data = json.loads(meta.read_text(encoding="utf-8"))
        records.append(
            BackupRecord(
                label=str(data["label"]),
                path=Path(str(data["path"])),
                sha256=str(data["sha256"]),
                created_at=str(data["created_at"]),
            )
        )
    return tuple(records)


def verify_backup(path: Path, *, expected_sha256: str) -> bool:
    """Return true when ``path`` still matches ``expected_sha256``."""
    if not path.exists():
        return False
    return _sha256(path) == expected_sha256


def restore_backup(path: Path, *, dest_dir: Path, expected_sha256: str) -> Path:
    """Verify and extract a backup archive into ``dest_dir``.

    The archive is only extracted after its digest matches. Members are checked
    for path traversal before extraction so a corrupted/malicious archive cannot
    write outside ``dest_dir``.
    """
    if not verify_backup(path, expected_sha256=expected_sha256):
        raise BackupError("backup digest mismatch")
    dest_dir.mkdir(parents=True, exist_ok=True)
    dest_root = dest_dir.resolve()
    with tarfile.open(path, "r:gz") as tar:
        members = tar.getmembers()
        for member in members:
            target = (dest_root / member.name).resolve()
            if target != dest_root and dest_root not in target.parents:
                raise BackupError(f"unsafe archive member {member.name!r}")
        tar.extractall(dest_root, members=members)
    return dest_dir


def _write_record(record: BackupRecord) -> None:
    data = {
        "label": record.label,
        "path": str(record.path),
        "sha256": record.sha256,
        "created_at": record.created_at,
    }
    record.path.with_suffix(record.path.suffix + ".json").write_text(
        json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return "sha256:" + h.hexdigest()


def _safe_label(label: str) -> str:
    cleaned = "".join(ch if ch.isalnum() or ch in {"-", "_"} else "-" for ch in label.lower())
    cleaned = "-".join(part for part in cleaned.split("-") if part)
    return cleaned or "backup"
