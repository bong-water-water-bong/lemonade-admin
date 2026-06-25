"""Stdlib HTTP server for the internal Lemonade admin app."""

from __future__ import annotations

from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

from lemonade_admin.app import AdminApp


class _AdminHandler(BaseHTTPRequestHandler):
    app: AdminApp

    def do_GET(self) -> None:  # noqa: N802 - BaseHTTPRequestHandler API
        host = self.headers.get("Host", "127.0.0.1")
        role = self.headers.get("X-Lemonade-Role", "owner")
        response = self.app.handle("GET", self.path, host=host, role=role)
        self.send_response(response.status)
        self.send_header("Content-Type", response.content_type)
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(response.body.encode("utf-8"))

    def log_message(self, format: str, *args: object) -> None:
        """Keep the admin server quiet unless wrapped by a richer logger."""
        return


def serve(app: AdminApp, *, host: str, port: int) -> None:
    """Serve ``app`` on an internal host/port until interrupted."""
    handler = type("AdminHandler", (_AdminHandler,), {"app": app})
    server = ThreadingHTTPServer((host, port), handler)
    try:
        server.serve_forever()
    finally:
        server.server_close()
