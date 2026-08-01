from __future__ import annotations

import argparse
import json
from pathlib import Path

from database.database import Database
from importer.archive_reader import scan_archive
from importer.betfair_parser import audit_archive, write_audit


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Betfair Cricket Research")
    sub = parser.add_subparsers(dest="command")

    init_cmd = sub.add_parser("init", help="Initialise a SQLite database")
    init_cmd.add_argument("database")

    scan_cmd = sub.add_parser("scan", help="Scan a TAR archive")
    scan_cmd.add_argument("archive")

    audit_cmd = sub.add_parser("audit", help="Parse Betfair market definitions")
    audit_cmd.add_argument("archive")
    audit_cmd.add_argument("--output", help="Optional .csv or .json output file")
    audit_cmd.add_argument("--limit", type=int, help="Only parse the first N BZ2 files")

    return parser


def main() -> int:
    args = build_parser().parse_args()

    if args.command == "init":
        Database(args.database).initialise()
        print(f"Database initialised: {args.database}")
        return 0

    if args.command == "scan":
        stats = scan_archive(args.archive)
        print(json.dumps(stats, indent=2))
        return 0

    if args.command == "audit":
        report = audit_archive(args.archive, limit=args.limit)
        print(json.dumps(report["summary"], indent=2))
        if args.output:
            write_audit(report["markets"], Path(args.output))
            print(f"Audit written to: {args.output}")
        return 0

    build_parser().print_help()
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
