from pathlib import Path

from lemonade_admin.backup import create_backup
from lemonade_admin.cli import main


def test_cli_can_restore_verified_backup(tmp_path: Path, capsys):
    data = tmp_path / "data"
    data.mkdir()
    (data / "state.json").write_text("before", encoding="utf-8")
    record = create_backup(paths=(data,), out_dir=tmp_path / "backups", label="pre-install")
    dest = tmp_path / "restore"

    code = main(
        [
            "--backup-restore",
            str(record.path),
            "--backup-digest",
            record.sha256,
            "--backup-restore-dest",
            str(dest),
        ]
    )

    assert code == 0
    assert "restored:" in capsys.readouterr().out
    assert (dest / "data" / "state.json").read_text(encoding="utf-8") == "before"
