from pathlib import Path

from lemonade_admin.app import AccessPolicy, AdminApp, HelpCenter
from lemonade_admin.backup import create_backup


def test_backups_route_lists_local_backup_records(tmp_path: Path, monkeypatch):
    docs = tmp_path / "docs"
    docs.mkdir()
    (docs / "operator.md").write_text("# Operator\nUse POS.", encoding="utf-8")
    data = tmp_path / "data"
    data.mkdir()
    (data / "state.json").write_text("{}", encoding="utf-8")
    backup_dir = tmp_path / "backups"
    create_backup(paths=(data,), out_dir=backup_dir, label="pre-install")
    monkeypatch.setenv("LEMONADE_BACKUP_DIR", str(backup_dir))
    app = AdminApp(help_center=HelpCenter(docs), policy=AccessPolicy())

    response = app.handle("GET", "/backups", host="127.0.0.1", role="owner")

    assert response.status == 200
    assert "Backups" in response.body
    assert "pre-install" in response.body
    assert "sha256:" in response.body


def test_attendant_cannot_view_backups(tmp_path: Path):
    docs = tmp_path / "docs"
    docs.mkdir()
    app = AdminApp(help_center=HelpCenter(docs), policy=AccessPolicy())

    response = app.handle("GET", "/backups", host="127.0.0.1", role="attendant")

    assert response.status == 403
