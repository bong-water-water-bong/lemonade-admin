from pathlib import Path

from lemonade_admin.cli import main


def test_cli_route_accepts_role_and_blocks_attendant_package_wizard(tmp_path: Path, capsys):
    docs = tmp_path / "docs"
    docs.mkdir()
    (docs / "operator.md").write_text("# Operator\nUse POS.", encoding="utf-8")

    code = main(["--docs", str(docs), "--route", "/packages", "--role", "attendant"])

    assert code == 1
    assert "owner/admin" in capsys.readouterr().out


def test_cli_route_can_preview_package_plan(tmp_path: Path, capsys):
    docs = tmp_path / "docs"
    docs.mkdir()
    (docs / "operator.md").write_text("# Operator\nUse POS.", encoding="utf-8")

    code = main(
        [
            "--docs",
            str(docs),
            "--route",
            "/packages/plan?profile=none&department=inventory",
            "--role",
            "admin",
        ]
    )

    assert code == 0
    out = capsys.readouterr().out
    assert "Install Plan" in out
    assert "inventory" in out
