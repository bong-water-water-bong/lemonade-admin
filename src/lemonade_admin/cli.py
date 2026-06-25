"""CLI helpers for the internal admin package."""

from __future__ import annotations

import argparse
from collections.abc import Sequence
from pathlib import Path

from lemonade_admin.app import AccessPolicy, AdminApp, HelpCenter
from lemonade_admin.server import serve


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="lemonade-admin")
    parser.add_argument("--docs", type=Path, default=Path("docs"))
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8788)
    parser.add_argument("--route", default="/")
    parser.add_argument("--role", choices=("owner", "admin", "attendant"), default="owner")
    parser.add_argument("--serve", action="store_true", help="Run the internal HTTP server.")
    args = parser.parse_args(argv)

    app = AdminApp(
        help_center=HelpCenter(args.docs), policy=AccessPolicy(host=args.host, port=args.port)
    )
    if args.serve:
        print(f"Serving Lemonade Admin on http://{args.host}:{args.port}")
        serve(app, host=args.host, port=args.port)
        return 0
    response = app.handle("GET", args.route, host=args.host, role=args.role)
    print(response.body)
    return 0 if response.status < 400 else 1


if __name__ == "__main__":
    raise SystemExit(main())
