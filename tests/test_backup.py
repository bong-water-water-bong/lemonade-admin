from pathlib import Path

from lemonade_admin.backup import BackupError, create_backup, list_backups, verify_backup


def test_create_backup_archives_selected_paths_and_verifies(tmp_path: Path):
    data = tmp_path / "data"
    data.mkdir()
    (data / "install-state.json").write_text('{"ok": true}\n', encoding="utf-8")
    out_dir = tmp_path / "backups"

    record = create_backup(paths=(data,), out_dir=out_dir, label="pre-install")

    assert record.path.exists()
    assert record.sha256.startswith("sha256:")
    assert record.label == "pre-install"
    assert verify_backup(record.path, expected_sha256=record.sha256)
    assert list_backups(out_dir)[0].path == record.path


def test_verify_backup_detects_tampering(tmp_path: Path):
    data = tmp_path / "data"
    data.mkdir()
    (data / "state.json").write_text("before", encoding="utf-8")
    record = create_backup(paths=(data,), out_dir=tmp_path / "backups", label="snapshot")

    with record.path.open("ab") as f:
        f.write(b"tamper")

    assert not verify_backup(record.path, expected_sha256=record.sha256)


def test_create_backup_requires_existing_paths(tmp_path: Path):
    missing = tmp_path / "missing"

    try:
        create_backup(paths=(missing,), out_dir=tmp_path / "backups", label="bad")
    except BackupError as exc:
        assert "does not exist" in str(exc)
    else:  # pragma: no cover - defensive
        raise AssertionError("expected BackupError")
