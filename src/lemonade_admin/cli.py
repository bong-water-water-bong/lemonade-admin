"""CLI helpers for the internal admin package."""

from __future__ import annotations

import argparse
from collections.abc import Sequence
from pathlib import Path

from lemonade_admin.app import AccessPolicy, AdminApp, HelpCenter
from lemonade_admin.backup import create_backup, list_backups
from lemonade_admin.server import serve


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="lemonade-admin")
    parser.add_argument("--docs", type=Path, default=Path("docs"))
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8788)
    parser.add_argument("--route", default="/")
    parser.add_argument("--role", choices=("owner", "admin", "attendant"), default="owner")
    parser.add_argument("--serve", action="store_true", help="Run the internal HTTP server.")
    parser.add_argument("--backup-list", action="store_true", help="List local backups and exit.")
    parser.add_argument(
        "--backup-create", action="store_true", help="Create a local backup and exit."
    )
    parser.add_argument(
        "--backup-path",
        action="append",
        default=[],
        type=Path,
        help="Path to include in a backup; can be repeated.",
    )
    parser.add_argument(
        "--backup-out",
        type=Path,
        default=Path.home() / ".lemonade" / "backups",
        help="Backup output/list directory.",
    )
    parser.add_argument("--backup-label", default="manual", help="Label for --backup-create.")
    args = parser.parse_args(argv)

    if args.backup_create:
        record = create_backup(
            paths=tuple(args.backup_path), out_dir=args.backup_out, label=args.backup_label
        )
        print(f"created: {record.path}")
        print(record.sha256)
        return 0
    if args.backup_list:
        backups = list_backups(args.backup_out)
        if not backups:
            print("No local backups found.")
            return 0
        for record in backups:
            print(f"{record.created_at} {record.label} {record.path} {record.sha256}")
        return 0

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
