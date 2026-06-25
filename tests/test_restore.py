from pathlib import Path

from lemonade_admin.backup import BackupError, create_backup, restore_backup, verify_backup


def test_restore_backup_verifies_digest_and_restores_contents(tmp_path: Path):
    data = tmp_path / "data"
    data.mkdir()
    (data / "state.json").write_text("before", encoding="utf-8")
    record = create_backup(paths=(data,), out_dir=tmp_path / "backups", label="pre-install")
    (data / "state.json").write_text("after", encoding="utf-8")
    restore_dir = tmp_path / "restore"

    restored = restore_backup(record.path, dest_dir=restore_dir, expected_sha256=record.sha256)

    assert restored == restore_dir
    assert (restore_dir / "data" / "state.json").read_text(encoding="utf-8") == "before"
    assert verify_backup(record.path, expected_sha256=record.sha256)


def test_restore_backup_rejects_tampered_archive(tmp_path: Path):
    data = tmp_path / "data"
    data.mkdir()
    (data / "state.json").write_text("before", encoding="utf-8")
    record = create_backup(paths=(data,), out_dir=tmp_path / "backups", label="pre-install")
    with record.path.open("ab") as f:
        f.write(b"tamper")

    try:
        restore_backup(record.path, dest_dir=tmp_path / "restore", expected_sha256=record.sha256)
    except BackupError as exc:
        assert "digest mismatch" in str(exc)
    else:  # pragma: no cover - defensive
        raise AssertionError("expected BackupError")


def test_restore_backup_rejects_path_traversal_members(tmp_path: Path):
    import tarfile

    archive = tmp_path / "bad.tar.gz"
    payload = tmp_path / "payload.txt"
    payload.write_text("bad", encoding="utf-8")
    with tarfile.open(archive, "w:gz") as tar:
        tar.add(payload, arcname="../escape.txt")
    # Compute a real digest so the traversal guard is what fails.
    from lemonade_admin.backup import _sha256  # pyright/mypy: private regression helper

    digest = _sha256(archive)

    try:
        restore_backup(archive, dest_dir=tmp_path / "restore", expected_sha256=digest)
    except BackupError as exc:
        assert "unsafe archive member" in str(exc)
    else:  # pragma: no cover - defensive
        raise AssertionError("expected BackupError")
