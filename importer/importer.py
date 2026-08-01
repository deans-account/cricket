from __future__ import annotations
import tarfile
from pathlib import Path
from typing import Any

from database.database import Database
from .common import DRAW_NAMES, norm, sha256_file
from .parser import first_definition, iter_messages
from .classifier import is_test_match


def _match_key(definition: dict) -> str:
    date = (definition.get("marketTime") or "")[:10]
    teams = sorted(
        norm(r.get("name")) for r in definition.get("runners", [])
        if norm(r.get("name")) not in DRAW_NAMES
    )
    return "|".join([date, *teams])


def _update_ladder(ladder: dict[float, float], updates: list | None) -> None:
    for item in updates or []:
        if not isinstance(item, list) or len(item) < 2:
            continue
        price, size = float(item[0]), float(item[1])
        if size <= 0:
            ladder.pop(price, None)
        else:
            ladder[price] = size


def _parse_full(raw_bz2: bytes) -> dict[str, Any]:
    market_id = None
    first_definition_obj = None
    final_definition = None
    first_pt = None
    last_pt = None
    current_inplay = None
    current_status = None
    market_total = None
    runner_defs: dict[int, dict] = {}
    state: dict[int, dict[str, Any]] = {}
    rows: list[tuple] = []

    for message in iter_messages(raw_bz2):
        pt = message.get("pt")
        if isinstance(pt, int):
            if first_pt is None:
                first_pt = pt
            last_pt = pt

        for change in message.get("mc", []):
            market_id = change.get("id", market_id)
            definition = change.get("marketDefinition")
            if definition:
                if first_definition_obj is None:
                    first_definition_obj = definition
                final_definition = definition
                current_inplay = definition.get("inPlay", current_inplay)
                current_status = definition.get("status", current_status)
                for runner in definition.get("runners", []):
                    sid = int(runner["id"])
                    runner_defs[sid] = {**runner_defs.get(sid, {}), **runner}
                    state.setdefault(sid, {
                        "ltp": None, "tv": None, "backs": {}, "lays": {}
                    })

            if "tv" in change:
                market_total = change.get("tv")

            for runner_change in change.get("rc", []):
                if pt is None:
                    continue
                sid = int(runner_change["id"])
                runner_state = state.setdefault(sid, {
                    "ltp": None, "tv": None, "backs": {}, "lays": {}
                })
                if "ltp" in runner_change:
                    runner_state["ltp"] = runner_change.get("ltp")
                if "tv" in runner_change:
                    runner_state["tv"] = runner_change.get("tv")
                if "atb" in runner_change:
                    _update_ladder(runner_state["backs"], runner_change.get("atb"))
                if "atl" in runner_change:
                    _update_ladder(runner_state["lays"], runner_change.get("atl"))

                best_back = max(runner_state["backs"], default=None)
                best_lay = min(runner_state["lays"], default=None)
                rows.append((
                    market_id, int(pt), sid,
                    runner_state["ltp"],
                    best_back,
                    runner_state["backs"].get(best_back) if best_back is not None else None,
                    best_lay,
                    runner_state["lays"].get(best_lay) if best_lay is not None else None,
                    runner_state["tv"], market_total,
                    int(bool(current_inplay)) if current_inplay is not None else None,
                    current_status,
                ))

    if not market_id or first_definition_obj is None:
        raise ValueError("No market definition found")

    return {
        "market_id": market_id,
        "first_definition": first_definition_obj,
        "final_definition": final_definition or first_definition_obj,
        "first_publish_time": first_pt,
        "last_publish_time": last_pt,
        "runner_defs": runner_defs,
        "price_rows": rows,
    }


def _log(con, import_id: int, severity: str, code: str, message: str, market_id=None) -> None:
    con.execute(
        "INSERT INTO integrity_log(import_id,market_id,severity,code,message) VALUES(?,?,?,?,?)",
        (import_id, market_id, severity, code, message),
    )


def import_archive(
    archive_path: str | Path,
    database_path: str | Path,
    limit: int | None = None,
) -> dict:
    archive_path = Path(archive_path)
    if not archive_path.exists():
        raise FileNotFoundError(archive_path)

    db = Database(database_path)
    db.initialise()
    digest = sha256_file(archive_path)

    with db.connect() as con:
        existing = con.execute(
            "SELECT id,status FROM imports WHERE archive_sha256=?", (digest,)
        ).fetchone()
        if existing and existing["status"] == "completed":
            return {
                "status": "already_imported",
                "archive": archive_path.name,
                "import_id": existing["id"],
            }
        if existing:
            import_id = existing["id"]
            con.execute(
                "UPDATE imports SET status='running',started_at=CURRENT_TIMESTAMP,completed_at=NULL WHERE id=?",
                (import_id,),
            )
        else:
            cur = con.execute(
                "INSERT INTO imports(archive_name,archive_sha256,status) VALUES(?,?,'running')",
                (archive_path.name, digest),
            )
            import_id = cur.lastrowid
        con.commit()

    counts = {
        "files_scanned": 0,
        "markets_imported": 0,
        "duplicates_skipped": 0,
        "errors": 0,
    }

    try:
        with tarfile.open(archive_path, "r:*") as archive, db.connect() as con:
            for member in archive:
                if not (member.isfile() and member.name.lower().endswith(".bz2")):
                    continue
                if limit is not None and counts["files_scanned"] >= limit:
                    break
                counts["files_scanned"] += 1
                if counts["files_scanned"] % 1000 == 0:
                    print(f"Scanned {counts['files_scanned']:,} market files; imported {counts['markets_imported']:,} Tests...")

                try:
                    handle = archive.extractfile(member)
                    if handle is None:
                        raise ValueError("Archive member could not be extracted")
                    raw = handle.read()
                    market_id, definition, _ = first_definition(raw)
                    if not definition or not market_id:
                        continue
                    is_test, reason = is_test_match(definition)
                    if not is_test:
                        continue

                    key = _match_key(definition)
                    duplicate = con.execute(
                        "SELECT market_id FROM markets WHERE market_id=? OR match_key=?",
                        (market_id, key),
                    ).fetchone()
                    if duplicate:
                        counts["duplicates_skipped"] += 1
                        continue

                    con.execute("SAVEPOINT market_import")
                    parsed = _parse_full(raw)
                    final_definition = parsed["final_definition"]
                    runners = definition.get("runners", [])
                    winner = next(
                        (int(r["id"]) for r in final_definition.get("runners", [])
                         if r.get("status") == "WINNER"),
                        None,
                    )
                    competition = definition.get("competition")
                    if isinstance(competition, dict):
                        competition = competition.get("name")

                    con.execute(
                        """
                        INSERT INTO markets(
                          market_id,match_key,event_name,market_name,market_type,market_time,
                          competition,country_code,source_import_id,source_member,
                          first_publish_time,last_publish_time,final_status,final_in_play,
                          winner_selection_id,settled
                        ) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
                        """,
                        (
                            market_id, key, definition.get("eventName"), definition.get("name"),
                            definition.get("marketType"), definition.get("marketTime"),
                            competition, definition.get("countryCode"), import_id, member.name,
                            parsed["first_publish_time"], parsed["last_publish_time"],
                            final_definition.get("status"),
                            int(bool(final_definition.get("inPlay"))) if "inPlay" in final_definition else None,
                            winner, int(winner is not None),
                        ),
                    )

                    team_index = 0
                    final_by_id = {int(r["id"]): r for r in final_definition.get("runners", [])}
                    for runner in runners:
                        sid = int(runner["id"])
                        name = runner.get("name", str(sid))
                        if norm(name) in DRAW_NAMES:
                            role = "draw"
                        else:
                            role = "home" if team_index == 0 else "away"
                            team_index += 1
                        final_runner = final_by_id.get(sid, runner)
                        con.execute(
                            "INSERT INTO runners VALUES(?,?,?,?,?,?)",
                            (market_id, sid, name, role, runner.get("sortPriority"), final_runner.get("status")),
                        )

                    valid_runner_ids = {int(r["id"]) for r in runners}
                    valid_rows = [
                        row for row in parsed["price_rows"]
                        if row[0] == market_id and row[2] in valid_runner_ids
                    ]
                    con.executemany(
                        "INSERT OR REPLACE INTO price_history VALUES(?,?,?,?,?,?,?,?,?,?,?,?)",
                        valid_rows,
                    )

                    if not valid_rows:
                        _log(con, import_id, "ERROR", "NO_PRICES", "No price changes found", market_id)
                    if winner is None:
                        _log(con, import_id, "WARNING", "UNSETTLED", "No winner found", market_id)

                    counts["markets_imported"] += 1
                    con.execute("RELEASE SAVEPOINT market_import")
                    if counts["markets_imported"] % 5 == 0:
                        con.commit()

                except Exception as exc:
                    try:
                        con.execute("ROLLBACK TO SAVEPOINT market_import")
                        con.execute("RELEASE SAVEPOINT market_import")
                    except Exception:
                        pass
                    counts["errors"] += 1
                    _log(con, import_id, "ERROR", "PARSE_ERROR", f"{member.name}: {exc}")

            con.execute(
                """
                UPDATE imports SET completed_at=CURRENT_TIMESTAMP,status='completed',
                  files_scanned=?,markets_imported=?,duplicates_skipped=?,errors=?
                WHERE id=?
                """,
                (
                    counts["files_scanned"], counts["markets_imported"],
                    counts["duplicates_skipped"], counts["errors"], import_id,
                ),
            )
            con.commit()

        return {"status": "completed", "archive": archive_path.name, "import_id": import_id, **counts}

    except Exception as exc:
        with db.connect() as con:
            con.execute(
                "UPDATE imports SET status='failed',completed_at=CURRENT_TIMESTAMP WHERE id=?",
                (import_id,),
            )
            _log(con, import_id, "ERROR", "IMPORT_FAILED", str(exc))
            con.commit()
        raise
