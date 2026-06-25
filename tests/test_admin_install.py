from pathlib import Path

from lemonade_store.bundle import build_bundle
from lemonade_store.package_manager import PackageManager

from lemonade_admin.app import AccessPolicy, AdminApp, HelpCenter


def _wheels(tmp_path: Path) -> Path:
    wheels = tmp_path / "artifacts"
    wheels.mkdir()
    (wheels / "lemonade_cashier-0.1.0-py3-none-any.whl").write_bytes(b"cashier wheel")
    (wheels / "lemonade_inventory-0.1.0-py3-none-any.whl").write_bytes(b"inventory wheel")
    return wheels


def _docs(tmp_path: Path) -> Path:
    docs = tmp_path / "docs"
    docs.mkdir()
    (docs / "operator.md").write_text("# Operator\nUse POS.", encoding="utf-8")
    return docs


def test_owner_admin_post_install_route_installs_from_manifest(tmp_path: Path):
    manifest = build_bundle(
        wheels_dir=_wheels(tmp_path),
        out_path=tmp_path / "lemonade-bundle.toml",
        suite_version="0.1.0",
        source="usb",
    )
    commands: list[list[str]] = []
    manager = PackageManager(
        state_path=tmp_path / "state.json",
        runner=lambda command: commands.append(command),
    )
    app = AdminApp(
        help_center=HelpCenter(_docs(tmp_path)),
        policy=AccessPolicy(),
        package_manager=manager,
    )

    response = app.handle(
        "POST",
        f"/packages/install?profile=none&department=inventory&manifest={manifest}&confirm=install",
        host="127.0.0.1",
        role="admin",
    )

    assert response.status == 200
    assert "Install Complete" in response.body
    assert "cashier" in response.body
    assert "inventory" in response.body
    assert len(commands) == 2


def test_install_route_requires_explicit_confirmation(tmp_path: Path):
    manager = PackageManager(state_path=tmp_path / "state.json", runner=lambda command: None)
    app = AdminApp(
        help_center=HelpCenter(_docs(tmp_path)),
        policy=AccessPolicy(),
        package_manager=manager,
    )

    response = app.handle(
        "POST",
        "/packages/install?manifest=/tmp/lemonade-bundle.toml&profile=store-operations",
        host="127.0.0.1",
        role="owner",
    )

    assert response.status == 400
    assert "confirm=install" in response.body


def test_install_route_rejects_attendant(tmp_path: Path):
    app = AdminApp(help_center=HelpCenter(_docs(tmp_path)), policy=AccessPolicy())

    response = app.handle(
        "POST",
        "/packages/install?manifest=/tmp/lemonade-bundle.toml&confirm=install",
        host="127.0.0.1",
        role="attendant",
    )

    assert response.status == 403
