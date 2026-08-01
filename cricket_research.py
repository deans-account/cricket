from __future__ import annotations

import argparse
import json
from pathlib import Path

from database.database import Database
from importer.archive_reader import scan_archive
from importer.betfair_parser import audit_archive, write_audit
from importer.importer import import_archive
from reports.reports import database_stats, verify_database


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Betfair Cricket Research")
    sub = parser.add_subparsers(dest="command")

    p = sub.add_parser("init", help="Initialise a SQLite database")
    p.add_argument("database")

    p = sub.add_parser("scan", help="Scan a TAR archive")
    p.add_argument("archive")

    p = sub.add_parser("audit", help="Audit market definitions")
    p.add_argument("archive")
    p.add_argument("--output", help="Optional .csv or .json output")
    p.add_argument("--limit", type=int)

    p = sub.add_parser("import", help="Import Test Match Odds markets")
    p.add_argument("archive")
    p.add_argument("--database", default="cricket_research.sqlite")
    p.add_argument("--limit", type=int, help="Only scan first N BZ2 files")
    p.add_argument(
        "--include-uncertain",
        action="store_true",
        help="Import uncertain Test classifications too",
    )

    p = sub.add_parser("stats", help="Show database totals")
    p.add_argument("--database", default="cricket_research.sqlite")

    p = sub.add_parser("verify", help="Run database integrity checks")
    p.add_argument("--database", default="cricket_research.sqlite")

    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    if args.command == "init":
        Database(args.database).initialise()
        print(f"Database initialised: {args.database}")
        return 0

    if args.command == "scan":
        print(json.dumps(scan_archive(args.archive), indent=2))
        return 0

    if args.command == "audit":
        report = audit_archive(args.archive, limit=args.limit)
        print(json.dumps(report["summary"], indent=2))
        if args.output:
            write_audit(report["markets"], Path(args.output))
            print(f"Audit written to: {args.output}")
        return 0

    if args.command == "import":
        summary = import_archive(
            archive_path=args.archive,
            database_path=args.database,
            limit=args.limit,
            include_uncertain=args.include_uncertain,
        )
        print(json.dumps(summary, indent=2))
        return 0 if summary["status"] == "completed" else 2

    if args.command == "stats":
        print(json.dumps(database_stats(args.database), indent=2))
        return 0

    if args.command == "verify":
        report = verify_database(args.database)
        print(json.dumps(report, indent=2))
        return 0 if report["healthy"] else 3

    parser.print_help()
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
