from pathlib import Path

from lemonade_store.bundle import build_bundle
from lemonade_store.package_manager import PackageManager

from lemonade_admin.app import AccessPolicy, AdminApp, HelpCenter


def test_admin_install_route_passes_signature_key_to_package_manager(tmp_path: Path):
    docs = tmp_path / "docs"
    docs.mkdir()
    wheels = tmp_path / "artifacts"
    wheels.mkdir()
    (wheels / "lemonade_cashier-0.1.0-py3-none-any.whl").write_bytes(b"cashier wheel")
    key = tmp_path / "bundle.key"
    key.write_bytes(b"owner-maintainer-secret")
    wrong_key = tmp_path / "wrong.key"
    wrong_key.write_bytes(b"wrong")
    manifest = build_bundle(
        wheels_dir=wheels,
        out_path=tmp_path / "lemonade-bundle.toml",
        suite_version="0.1.0",
        source="usb",
        signature_key_path=key,
    )
    manager = PackageManager(state_path=tmp_path / "state.json", runner=lambda command: None)
    app = AdminApp(help_center=HelpCenter(docs), policy=AccessPolicy(), package_manager=manager)

    bad = app.handle(
        "POST",
        f"/packages/install?profile=none&department=cashier&manifest={manifest}&key={wrong_key}&confirm=install",
        host="127.0.0.1",
        role="owner",
    )
    good = app.handle(
        "POST",
        f"/packages/install?profile=none&department=cashier&manifest={manifest}&key={key}&confirm=install",
        host="127.0.0.1",
        role="owner",
    )

    assert bad.status == 400
    assert "signature mismatch" in bad.body
    assert good.status == 200
