from pathlib import Path

from lemonade_admin.cli import main


def test_cli_can_create_and_list_backups(tmp_path: Path, capsys):
    data = tmp_path / "data"
    data.mkdir()
    (data / "state.json").write_text("{}", encoding="utf-8")
    backups = tmp_path / "backups"

    create_code = main(
        [
            "--backup-create",
            "--backup-path",
            str(data),
            "--backup-out",
            str(backups),
            "--backup-label",
            "pre-install",
        ]
    )
    assert create_code == 0
    assert "sha256:" in capsys.readouterr().out

    list_code = main(["--backup-list", "--backup-out", str(backups)])
    assert list_code == 0
    out = capsys.readouterr().out
    assert "pre-install" in out
    assert "sha256:" in out
