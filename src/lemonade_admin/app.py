"""Stdlib-only internal admin web shell primitives.

This module intentionally avoids a framework in the first commit so the package
has a small, testable core. A future UI server can wrap ``AdminApp`` with
FastAPI or another framework without changing package-manager semantics.
"""

from __future__ import annotations

import ipaddress
from dataclasses import dataclass
from pathlib import Path

from lemonade_store.package_manager import build_catalog


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

    def handle(self, method: str, path: str, *, host: str) -> Response:
        """Handle a minimal internal route."""
        if not self.policy.is_internal_host(host):
            return Response(status=403, body="Forbidden: internal access only")
        if method != "GET":
            return Response(status=405, body="Method not allowed")
        if path == "/":
            return Response(status=200, body=self._home())
        if path == "/packages":
            return Response(status=200, body=self._packages())
        if path == "/help":
            return Response(status=200, body=self._help_index())
        if path.startswith("/help/"):
            return Response(status=200, body=self.help_center.render(path.rsplit("/", 1)[-1]))
        return Response(status=404, body="Not found")

    def _home(self) -> str:
        return "<h1>Lemonade Admin</h1><p>Internal-only POS/admin shell.</p>"

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
        return f"<h1>Package Wizard</h1><h2>Profiles</h2><ul>{profiles}</ul><h2>Departments</h2><ul>{departments}</ul>"

    def _help_index(self) -> str:
        entries = "".join(
            f"<li>{entry['title']} ({entry['audience']})</li>" for entry in self.help_center.index()
        )
        return f"<h1>Help Center</h1><ul>{entries}</ul>"


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
