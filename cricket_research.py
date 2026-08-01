from __future__ import annotations
import argparse
import json

from database.database import Database
from importer.importer import import_archive
from reports.reports import database_stats, verify_database
from reports.derive import build_market_summary
from reports.exporter import export_market_summary


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Betfair Cricket Research v0.8")
    sub = parser.add_subparsers(dest="command")

    p = sub.add_parser("init", help="Create the SQLite database")
    p.add_argument("database")

    p = sub.add_parser("import", help="Import a Betfair TAR archive")
    p.add_argument("archive")
    p.add_argument("--database", default="cricket_research.sqlite")
    p.add_argument("--limit", type=int, help="Only scan the first N BZ2 files")

    p = sub.add_parser("stats", help="Show database totals and month coverage")
    p.add_argument("--database", default="cricket_research.sqlite")

    p = sub.add_parser("verify", help="Verify database integrity")
    p.add_argument("--database", default="cricket_research.sqlite")

    p = sub.add_parser("derive", help="Build compact per-match research summaries")
    p.add_argument("--database", default="cricket_research.sqlite")

    p = sub.add_parser("export", help="Export compact match summaries to CSV")
    p.add_argument("output")
    p.add_argument("--database", default="cricket_research.sqlite")
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    if args.command == "init":
        Database(args.database).initialise()
        print(f"Created: {args.database}")
        return 0
    if args.command == "import":
        result = import_archive(args.archive, args.database, args.limit)
        print(json.dumps(result, indent=2))
        return 0
    if args.command == "stats":
        print(json.dumps(database_stats(args.database), indent=2))
        return 0
    if args.command == "verify":
        result = verify_database(args.database)
        print(json.dumps(result, indent=2))
        return 0 if result["healthy"] else 2
    if args.command == "derive":
        print(json.dumps(build_market_summary(args.database), indent=2))
        return 0
    if args.command == "export":
        print(json.dumps(export_market_summary(args.database, args.output), indent=2))
        return 0

    parser.print_help()
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
