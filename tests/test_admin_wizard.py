from pathlib import Path

from lemonade_admin.app import AccessPolicy, AdminApp, HelpCenter


def _app(tmp_path: Path) -> AdminApp:
    docs = tmp_path / "docs"
    docs.mkdir()
    (docs / "operator.md").write_text("# Operator\nUse POS.", encoding="utf-8")
    return AdminApp(help_center=HelpCenter(docs), policy=AccessPolicy())


def test_attendant_can_use_home_and_help_but_not_package_wizard(tmp_path: Path):
    app = _app(tmp_path)

    home = app.handle("GET", "/", host="127.0.0.1", role="attendant")
    help_page = app.handle("GET", "/help", host="127.0.0.1", role="attendant")
    packages = app.handle("GET", "/packages", host="127.0.0.1", role="attendant")

    assert home.status == 200
    assert help_page.status == 200
    assert packages.status == 403
    assert "owner/admin" in packages.body


def test_package_wizard_plan_route_resolves_profile_department_and_agent(tmp_path: Path):
    app = _app(tmp_path)

    response = app.handle(
        "GET",
        "/packages/plan?profile=none&department=inventory&agent=onboarder",
        host="127.0.0.1",
        role="owner",
    )

    assert response.status == 200
    assert "Install Plan" in response.body
    assert "cashier" in response.body
    assert "inventory" in response.body
    assert "onboarder" in response.body
    assert "lemonade-agents" in response.body


def test_package_wizard_status_uses_local_state_file(tmp_path: Path, monkeypatch):
    from lemonade_store.package_manager import InstallState

    state_path = tmp_path / "state.json"
    state = InstallState()
    state.record_install("cashier", "lemonade-cashier", "0.1.0", "sha256:abc")
    state.save(state_path)
    monkeypatch.setenv("LEMONADE_STATE_PATH", str(state_path))
    app = _app(tmp_path)

    response = app.handle("GET", "/packages/status", host="127.0.0.1", role="admin")

    assert response.status == 200
    assert "Package Status" in response.body
    assert "cashier" in response.body
    assert "enabled" in response.body


def test_unknown_wizard_selection_returns_bad_request(tmp_path: Path):
    app = _app(tmp_path)

    response = app.handle(
        "GET",
        "/packages/plan?profile=none&department=badger",
        host="127.0.0.1",
        role="admin",
    )

    assert response.status == 400
    assert "unknown package" in response.body
