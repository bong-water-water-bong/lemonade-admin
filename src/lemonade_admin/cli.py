"""CLI helpers for the internal admin package."""

from __future__ import annotations

import argparse
from collections.abc import Sequence
from pathlib import Path

from lemonade_admin.app import AccessPolicy, AdminApp, HelpCenter


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="lemonade-admin")
    parser.add_argument("--docs", type=Path, default=Path("docs"))
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--route", default="/")
    args = parser.parse_args(argv)

    app = AdminApp(help_center=HelpCenter(args.docs), policy=AccessPolicy())
    response = app.handle("GET", args.route, host=args.host)
    print(response.body)
    return 0 if response.status < 400 else 1


if __name__ == "__main__":
    raise SystemExit(main())
