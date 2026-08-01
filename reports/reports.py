from __future__ import annotations
from database.database import Database


def database_stats(path: str) -> dict:
    db = Database(path)
    db.initialise()
    with db.connect() as con:
        coverage = [dict(r) for r in con.execute(
            "SELECT substr(market_time,1,7) AS month,COUNT(*) AS markets FROM markets GROUP BY month ORDER BY month"
        )]
        return {
            "imports": con.execute("SELECT COUNT(*) FROM imports").fetchone()[0],
            "markets": con.execute("SELECT COUNT(*) FROM markets").fetchone()[0],
            "runners": con.execute("SELECT COUNT(*) FROM runners").fetchone()[0],
            "price_rows": con.execute("SELECT COUNT(*) FROM price_history").fetchone()[0],
            "settled": con.execute("SELECT COUNT(*) FROM markets WHERE settled=1").fetchone()[0],
            "unsettled": con.execute("SELECT COUNT(*) FROM markets WHERE settled=0").fetchone()[0],
            "coverage": coverage,
        }


def verify_database(path: str) -> dict:
    db = Database(path)
    db.initialise()
    checks = []
    with db.connect() as con:
        integrity = con.execute("PRAGMA integrity_check").fetchone()[0]
        checks.append({"name": "sqlite_integrity", "passed": integrity == "ok", "detail": integrity})

        duplicate_markets = con.execute(
            "SELECT COUNT(*) FROM (SELECT market_id FROM markets GROUP BY market_id HAVING COUNT(*)>1)"
        ).fetchone()[0]
        checks.append({"name": "duplicate_market_ids", "passed": duplicate_markets == 0, "detail": duplicate_markets})

        duplicate_matches = con.execute(
            "SELECT COUNT(*) FROM (SELECT match_key FROM markets GROUP BY match_key HAVING COUNT(*)>1)"
        ).fetchone()[0]
        checks.append({"name": "duplicate_match_keys", "passed": duplicate_matches == 0, "detail": duplicate_matches})

        wrong_runners = con.execute(
            """
            SELECT COUNT(*) FROM (
              SELECT m.market_id FROM markets m LEFT JOIN runners r ON r.market_id=m.market_id
              GROUP BY m.market_id HAVING COUNT(r.selection_id)<>3
            )
            """
        ).fetchone()[0]
        checks.append({"name": "three_runners_per_market", "passed": wrong_runners == 0, "detail": wrong_runners})

        no_prices = con.execute(
            "SELECT COUNT(*) FROM markets m WHERE NOT EXISTS(SELECT 1 FROM price_history p WHERE p.market_id=m.market_id)"
        ).fetchone()[0]
        checks.append({"name": "price_history_present", "passed": no_prices == 0, "detail": no_prices})

        parse_errors = con.execute(
            "SELECT COUNT(*) FROM integrity_log WHERE severity='ERROR'"
        ).fetchone()[0]
        checks.append({"name": "logged_errors", "passed": parse_errors == 0, "detail": parse_errors})

    return {"healthy": all(c["passed"] for c in checks), "checks": checks}
