from __future__ import annotations

import sqlite3
from pathlib import Path

from database.database import Database


def _scalar(connection: sqlite3.Connection, query: str, params=()):
    row = connection.execute(query, params).fetchone()
    return row[0] if row else None


def database_stats(database_path: str | Path) -> dict:
    database = Database(database_path)
    database.initialise()
    with database.connect() as connection:
        coverage = connection.execute(
            """
            SELECT substr(market_time, 1, 7) AS month, COUNT(*) AS markets
            FROM markets
            WHERE market_time IS NOT NULL
            GROUP BY month
            ORDER BY month
            """
        ).fetchall()
        return {
            "database": str(database_path),
            "imports": _scalar(connection, "SELECT COUNT(*) FROM imports"),
            "markets": _scalar(connection, "SELECT COUNT(*) FROM markets"),
            "runners": _scalar(connection, "SELECT COUNT(*) FROM runners"),
            "price_rows": _scalar(connection, "SELECT COUNT(*) FROM price_history"),
            "settled_markets": _scalar(
                connection, "SELECT COUNT(*) FROM markets WHERE settled = 1"
            ),
            "unsettled_markets": _scalar(
                connection, "SELECT COUNT(*) FROM markets WHERE settled = 0"
            ),
            "confirmed_tests": _scalar(
                connection,
                "SELECT COUNT(*) FROM markets WHERE classification = 'confirmed_test'",
            ),
            "uncertain_tests": _scalar(
                connection,
                "SELECT COUNT(*) FROM markets WHERE classification = 'uncertain_test'",
            ),
            "coverage": [dict(row) for row in coverage],
        }


def verify_database(database_path: str | Path) -> dict:
    database = Database(database_path)
    database.initialise()
    checks = []

    with database.connect() as connection:
        integrity = _scalar(connection, "PRAGMA integrity_check")
        checks.append({
            "name": "sqlite_integrity",
            "passed": integrity == "ok",
            "detail": integrity,
        })

        duplicate_markets = _scalar(
            connection,
            """
            SELECT COUNT(*) FROM (
                SELECT market_id FROM markets GROUP BY market_id HAVING COUNT(*) > 1
            )
            """,
        )
        checks.append({
            "name": "duplicate_market_ids",
            "passed": duplicate_markets == 0,
            "detail": duplicate_markets,
        })

        wrong_runner_count = _scalar(
            connection,
            """
            SELECT COUNT(*) FROM (
                SELECT m.market_id
                FROM markets m
                LEFT JOIN runners r ON r.market_id = m.market_id
                GROUP BY m.market_id
                HAVING COUNT(r.selection_id) != 3
            )
            """,
        )
        checks.append({
            "name": "three_runners_per_market",
            "passed": wrong_runner_count == 0,
            "detail": wrong_runner_count,
        })

        no_prices = _scalar(
            connection,
            """
            SELECT COUNT(*)
            FROM markets m
            WHERE NOT EXISTS (
                SELECT 1 FROM price_history p WHERE p.market_id = m.market_id
            )
            """,
        )
        checks.append({
            "name": "price_history_present",
            "passed": no_prices == 0,
            "detail": no_prices,
        })

        orphan_prices = _scalar(
            connection,
            """
            SELECT COUNT(*)
            FROM price_history p
            LEFT JOIN markets m ON m.market_id = p.market_id
            WHERE m.market_id IS NULL
            """,
        )
        checks.append({
            "name": "orphan_price_rows",
            "passed": orphan_prices == 0,
            "detail": orphan_prices,
        })

        unresolved_warnings = _scalar(
            connection,
            "SELECT COUNT(*) FROM integrity_log WHERE severity IN ('WARNING','ERROR')",
        )
        checks.append({
            "name": "integrity_log_warnings",
            "passed": unresolved_warnings == 0,
            "detail": unresolved_warnings,
        })

    return {
        "database": str(database_path),
        "healthy": all(check["passed"] for check in checks),
        "checks": checks,
    }
