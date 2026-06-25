from pathlib import Path

from lemonade_admin.app import AccessPolicy, AdminApp, HelpCenter


def test_access_policy_defaults_to_internal_only():
    policy = AccessPolicy()

    assert policy.host == "127.0.0.1"
    assert policy.is_internal_host("127.0.0.1")
    assert policy.is_internal_host("localhost")
    assert policy.is_internal_host("192.168.1.25")
    assert not policy.is_internal_host("example.com")


def test_help_center_indexes_operator_admin_and_developer_docs(tmp_path: Path):
    docs = tmp_path / "docs"
    docs.mkdir()
    (docs / "operator.md").write_text("# Operator\nUse POS.", encoding="utf-8")
    (docs / "developer.md").write_text("# Developer\nMaintainer details.", encoding="utf-8")
    help_center = HelpCenter(docs)

    entries = help_center.index()

    assert entries == (
        {"slug": "developer", "title": "Developer", "audience": "developer"},
        {"slug": "operator", "title": "Operator", "audience": "operator"},
    )
    assert "Use POS" in help_center.render("operator")


def test_admin_app_routes_are_internal_and_include_package_wizard(tmp_path: Path):
    docs = tmp_path / "docs"
    docs.mkdir()
    (docs / "operator.md").write_text("# Operator\nUse POS.", encoding="utf-8")
    app = AdminApp(help_center=HelpCenter(docs), policy=AccessPolicy())

    response = app.handle("GET", "/", host="127.0.0.1")
    wizard = app.handle("GET", "/packages", host="127.0.0.1")
    forbidden = app.handle("GET", "/", host="public.example.com")

    assert response.status == 200
    assert "Lemonade Admin" in response.body
    assert wizard.status == 200
    assert "Package Wizard" in wizard.body
    assert "store-operations" in wizard.body
    assert forbidden.status == 403
