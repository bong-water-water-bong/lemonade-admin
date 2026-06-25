"""Stdlib-only internal admin web shell primitives.

This module intentionally avoids a framework in the first commit so the package
has a small, testable core. A future UI server can wrap ``AdminApp`` with
FastAPI or another framework without changing package-manager semantics.
"""

from __future__ import annotations

import html
import ipaddress
import os
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import parse_qs, urlsplit

from lemonade_store.package_manager import (
    CatalogError,
    InstallStateError,
    PackageManager,
    build_catalog,
    resolve_selection,
)

from lemonade_admin.backup import list_backups


@dataclass(frozen=True)
class Response:
    """Simple response object for the internal app shell."""

    status: int
    body: str
    content_type: str = "text/html; charset=utf-8"


@dataclass(frozen=True)
class AccessPolicy:
    """Internal-only host policy for localhost and private LAN clients."""

    host: str = "127.0.0.1"
    port: int = 8788
    allow_lan: bool = True

    def is_internal_host(self, host: str) -> bool:
        """Return true for localhost and private LAN hostnames/IPs."""
        hostname = host.split(":", 1)[0].lower()
        if hostname in {"127.0.0.1", "localhost", "::1"}:
            return True
        try:
            ip = ipaddress.ip_address(hostname)
        except ValueError:
            return False
        return self.allow_lan and ip.is_private


class HelpCenter:
    """Markdown-backed local Help Center index."""

    def __init__(self, docs_root: str | Path) -> None:
        self.docs_root = Path(docs_root)

    def index(self) -> tuple[dict[str, str], ...]:
        """Return sorted docs entries with slug, title, and audience."""
        entries: list[dict[str, str]] = []
        for path in sorted(self.docs_root.glob("*.md")):
            entries.append(
                {
                    "slug": path.stem,
                    "title": _title(path),
                    "audience": _audience(path.stem),
                }
            )
        return tuple(entries)

    def render(self, slug: str) -> str:
        """Render a markdown file as escaped preformatted text for now."""
        path = self.docs_root / f"{slug}.md"
        if not path.exists():
            return "# Not found\n"
        return path.read_text(encoding="utf-8")


class AdminApp:
    """Internal admin app shell used by CLI/server adapters."""

    def __init__(self, *, help_center: HelpCenter, policy: AccessPolicy | None = None) -> None:
        self.help_center = help_center
        self.policy = policy or AccessPolicy()

    def handle(self, method: str, path: str, *, host: str, role: str = "owner") -> Response:
        """Handle a minimal internal route."""
        if not self.policy.is_internal_host(host):
            return Response(status=403, body="Forbidden: internal access only")
        if method != "GET":
            return Response(status=405, body="Method not allowed")

        parsed = urlsplit(path)
        route = parsed.path
        query = parse_qs(parsed.query)

        if route == "/":
            return Response(status=200, body=self._home(role))
        if route == "/packages":
            denied = _require_owner_admin(role)
            if denied is not None:
                return denied
            return Response(status=200, body=self._packages())
        if route == "/packages/plan":
            denied = _require_owner_admin(role)
            if denied is not None:
                return denied
            return self._package_plan(query)
        if route == "/packages/status":
            denied = _require_owner_admin(role)
            if denied is not None:
                return denied
            return self._package_status()
        if route == "/backups":
            denied = _require_owner_admin(role)
            if denied is not None:
                return denied
            return self._backups()
        if route == "/help":
            return Response(status=200, body=self._help_index())
        if route.startswith("/help/"):
            return Response(status=200, body=self.help_center.render(route.rsplit("/", 1)[-1]))
        return Response(status=404, body="Not found")

    def _home(self, role: str) -> str:
        return (
            "<h1>Lemonade Admin</h1>"
            "<p>Internal-only POS/admin shell.</p>"
            f"<p>Role: {html.escape(role)}</p>"
            '<nav><a href="/help">Help Center</a> '
            '<a href="/packages">Package Wizard</a></nav>'
        )

    def _packages(self) -> str:
        catalog = build_catalog()
        profiles = "".join(
            f"<li>{profile.name}: {profile.label}</li>" for profile in catalog.profiles.values()
        )
        departments = "".join(
            f"<li>{pkg.name}: {pkg.distribution}</li>"
            for pkg in catalog.packages.values()
            if pkg.kind == "department"
        )
        return (
            "<h1>Package Wizard</h1>"
            "<p>Owner/admin only. Attendants can use POS and Help Center pages, "
            "but cannot install, disable, uninstall, export, publish, or change agents.</p>"
            '<p><a href="/packages/plan?profile=store-operations">Preview Store operations</a></p>'
            '<p><a href="/packages/status">View local package status</a></p>'
            f"<h2>Profiles</h2><ul>{profiles}</ul><h2>Departments</h2><ul>{departments}</ul>"
        )

    def _package_plan(self, query: dict[str, list[str]]) -> Response:
        profile_value = _first(query, "profile", "store-operations")
        profile: str | None = profile_value
        if profile_value in {"none", "custom", ""}:
            profile = None
        departments = tuple(query.get("department", ()))
        agents = tuple(query.get("agent", ()))
        try:
            selection = resolve_selection(profile=profile, departments=departments, agents=agents)
        except CatalogError as exc:
            return Response(status=400, body=f"Bad request: {html.escape(str(exc))}")

        package_items = "".join(f"<li>{html.escape(name)}</li>" for name in selection.package_names)
        distribution_items = "".join(
            f"<li>{html.escape(distribution)}</li>" for distribution in selection.distributions
        )
        return Response(
            status=200,
            body=(
                "<h1>Install Plan</h1>"
                f"<p>Profile: {html.escape(selection.profile or 'custom')}</p>"
                f"<h2>Packages</h2><ul>{package_items}</ul>"
                f"<h2>Distributions</h2><ul>{distribution_items}</ul>"
            ),
        )

    def _package_status(self) -> Response:
        try:
            status = _manager().status()
        except InstallStateError as exc:
            return Response(status=500, body=f"Install state error: {html.escape(str(exc))}")
        if not status:
            return Response(status=200, body="<h1>Package Status</h1><p>No packages installed.</p>")
        rows = "".join(
            "<tr>"
            f"<td>{html.escape(package.name)}</td>"
            f"<td>{html.escape(package.distribution)}</td>"
            f"<td>{html.escape(package.version)}</td>"
            f"<td>{'enabled' if package.enabled else 'disabled'}</td>"
            "</tr>"
            for package in status.values()
        )
        return Response(
            status=200,
            body=(
                "<h1>Package Status</h1>"
                "<table><thead><tr><th>Name</th><th>Distribution</th>"
                "<th>Version</th><th>State</th></tr></thead>"
                f"<tbody>{rows}</tbody></table>"
            ),
        )

    def _backups(self) -> Response:
        backup_dir = Path(
            os.environ.get("LEMONADE_BACKUP_DIR", str(Path.home() / ".lemonade" / "backups"))
        )
        backups = list_backups(backup_dir)
        if not backups:
            return Response(status=200, body="<h1>Backups</h1><p>No local backups found.</p>")
        rows = "".join(
            "<tr>"
            f"<td>{html.escape(record.label)}</td>"
            f"<td>{html.escape(record.created_at)}</td>"
            f"<td>{html.escape(str(record.path))}</td>"
            f"<td>{html.escape(record.sha256)}</td>"
            "</tr>"
            for record in backups
        )
        return Response(
            status=200,
            body=(
                "<h1>Backups</h1>"
                "<table><thead><tr><th>Label</th><th>Created</th>"
                "<th>Path</th><th>SHA-256</th></tr></thead>"
                f"<tbody>{rows}</tbody></table>"
            ),
        )

    def _help_index(self) -> str:
        entries = "".join(
            f"<li>{entry['title']} ({entry['audience']})</li>" for entry in self.help_center.index()
        )
        return f"<h1>Help Center</h1><ul>{entries}</ul>"


def _manager() -> PackageManager:
    state_path = os.environ.get("LEMONADE_STATE_PATH")
    if state_path:
        return PackageManager(state_path=state_path)
    return PackageManager()


def _first(query: dict[str, list[str]], key: str, default: str) -> str:
    values = query.get(key)
    if not values:
        return default
    return values[0]


def _require_owner_admin(role: str) -> Response | None:
    if role in {"owner", "admin"}:
        return None
    return Response(status=403, body="Forbidden: owner/admin role required")


def _title(path: Path) -> str:
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.startswith("# "):
            return line[2:].strip()
    return path.stem.replace("-", " ").title()


def _audience(slug: str) -> str:
    if "developer" in slug:
        return "developer"
    if "admin" in slug:
        return "admin"
    return "operator"
