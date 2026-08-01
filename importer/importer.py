from __future__ import annotations

import tarfile
from pathlib import Path
from typing import Any

from database.database import Database
from importer.archive_reader import sha256_file
from importer.betfair_parser import iter_messages, metadata_from_definition
from importer.market_filter import classify_test_match


def _best_price(levels: list, side: str) -> tuple[float | None, float | None]:
    if not levels:
        return None, None
    valid = [x for x in levels if isinstance(x, list) and len(x) >= 2 and x[1] > 0]
    if not valid:
        return None, None
    item = max(valid, key=lambda x: x[0]) if side == "back" else min(valid, key=lambda x: x[0])
    return float(item[0]), float(item[1])


def _extract_updates(raw_bz2: bytes) -> dict[str, Any]:
    market_id = None
    current_definition = None
    first_publish_time = None
    last_publish_time = None
    metadata = None
    runners: dict[int, dict[str, Any]] = {}
    prices: list[tuple] = []
    settlements: dict[int, tuple[str | None, int | None]] = {}
    current_in_play = None
    current_status = None

    for message in iter_messages(raw_bz2):
        pt = message.get("pt")
        if isinstance(pt, int):
            first_publish_time = pt if first_publish_time is None else first_publish_time
            last_publish_time = pt

        if message.get("op") != "mcm":
            continue

        for mc in message.get("mc", []):
            market_id = mc.get("id", market_id)
            definition = mc.get("marketDefinition")
            if definition:
                current_definition = definition
                current_in_play = definition.get("inPlay", current_in_play)
                current_status = definition.get("status", current_status)
                metadata = metadata_from_definition(
                    market_id, definition, "", first_publish_time
                )
                for runner in definition.get("runners", []):
                    selection_id = runner.get("id")
                    if selection_id is None:
                        continue
                    runners[int(selection_id)] = {
                        "selection_id": int(selection_id),
                        "runner_name": runner.get("name"),
                        "sort_priority": runner.get("sortPriority"),
                        "status": runner.get("status"),
                        "adjustment_factor": runner.get("adjustmentFactor"),
                    }
                    if runner.get("status") in {"WINNER", "LOSER", "REMOVED"}:
                        settlements[int(selection_id)] = (runner.get("status"), pt)

            for rc in mc.get("rc", []):
                selection_id = rc.get("id")
                if selection_id is None or pt is None:
                    continue
                atb = rc.get("atb") or []
                atl = rc.get("atl") or []
                best_back_price, best_back_size = _best_price(atb, "back")
                best_lay_price, best_lay_size = _best_price(atl, "lay")
                prices.append((
                    market_id,
                    int(pt),
                    int(selection_id),
                    rc.get("ltp"),
                    rc.get("tv"),
                    best_back_price,
                    best_back_size,
                    best_lay_price,
                    best_lay_size,
                    int(bool(current_in_play)) if current_in_play is not None else None,
                    current_status,
                ))

    if metadata is None or current_definition is None or market_id is None:
        raise ValueError("Market definition not found")

    metadata["first_publish_time"] = first_publish_time
    metadata["last_publish_time"] = last_publish_time
    return {
        "market_id": market_id,
        "metadata": metadata,
        "runners": list(runners.values()),
        "prices": prices,
        "settlements": settlements,
    }


def _log(connection, import_id, severity, code, message, market_id=None):
    connection.execute(
        """
        INSERT INTO integrity_log(import_id, market_id, severity, code, message)
        VALUES (?, ?, ?, ?, ?)
        """,
        (import_id, market_id, severity, code, message),
    )


def import_archive(
    archive_path: str | Path,
    database_path: str | Path,
    limit: int | None = None,
    include_uncertain: bool = False,
) -> dict:
    archive_path = Path(archive_path)
    database = Database(database_path)
    database.initialise()
    archive_hash = sha256_file(archive_path)

    with database.connect() as connection:
        existing = connection.execute(
            "SELECT id, status FROM imports WHERE archive_sha256 = ?",
            (archive_hash,),
        ).fetchone()
        if existing and existing["status"] == "completed":
            return {
                "status": "already_imported",
                "archive": archive_path.name,
                "import_id": existing["id"],
            }

        cursor = connection.execute(
            """
            INSERT OR REPLACE INTO imports(
                id, archive_name, archive_path, archive_sha256, status
            )
            VALUES (
                COALESCE((SELECT id FROM imports WHERE archive_sha256 = ?), NULL),
                ?, ?, ?, 'running'
            )
            """,
            (archive_hash, archive_path.name, str(archive_path), archive_hash),
        )
        import_id = cursor.lastrowid
        if not import_id:
            import_id = connection.execute(
                "SELECT id FROM imports WHERE archive_sha256 = ?",
                (archive_hash,),
            ).fetchone()["id"]
        connection.commit()

    counts = {
        "files_scanned": 0,
        "markets_parsed": 0,
        "test_markets_found": 0,
        "markets_imported": 0,
        "duplicates_skipped": 0,
        "errors": 0,
        "uncertain_skipped": 0,
    }

    try:
        with tarfile.open(archive_path, "r:*") as archive, database.connect() as connection:
            for member in archive:
                if not member.isfile() or not member.name.lower().endswith(".bz2"):
                    continue
                if limit is not None and counts["files_scanned"] >= limit:
                    break

                counts["files_scanned"] += 1
                extracted = archive.extractfile(member)
                if extracted is None:
                    counts["errors"] += 1
                    _log(connection, import_id, "ERROR", "EXTRACT_FAILED", member.name)
                    continue

                try:
                    raw = extracted.read()
                    parsed = _extract_updates(raw)
                    counts["markets_parsed"] += 1
                    metadata = parsed["metadata"]
                    metadata["source_file"] = member.name
                    classification, reason = classify_test_match(metadata)

                    if classification == "excluded":
                        continue

                    counts["test_markets_found"] += 1
                    if classification == "uncertain_test" and not include_uncertain:
                        counts["uncertain_skipped"] += 1
                        _log(
                            connection, import_id, "WARNING", "UNCERTAIN_TEST",
                            f"{metadata.get('event_name')}: {reason}",
                            parsed["market_id"],
                        )
                        continue

                    exists = connection.execute(
                        "SELECT 1 FROM markets WHERE market_id = ?",
                        (parsed["market_id"],),
                    ).fetchone()
                    if exists:
                        counts["duplicates_skipped"] += 1
                        continue

                    winner_ids = [
                        selection_id
                        for selection_id, (status, _) in parsed["settlements"].items()
                        if status == "WINNER"
                    ]
                    winner_id = winner_ids[0] if len(winner_ids) == 1 else None
                    settled = int(bool(parsed["settlements"]))

                    connection.execute(
                        """
                        INSERT INTO markets(
                            market_id, event_name, market_name, market_type, market_time,
                            event_type_id, competition, country_code, timezone,
                            number_of_winners, status, in_play, classification,
                            classification_reason, source_import_id, settled,
                            winner_selection_id, first_publish_time, last_publish_time
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """,
                        (
                            parsed["market_id"], metadata.get("event_name"),
                            metadata.get("market_name"), metadata.get("market_type"),
                            metadata.get("market_time"), metadata.get("event_type_id"),
                            metadata.get("competition"), metadata.get("country_code"),
                            metadata.get("timezone"), metadata.get("number_of_winners"),
                            metadata.get("status"), int(bool(metadata.get("in_play")))
                            if metadata.get("in_play") is not None else None,
                            classification, reason, import_id, settled, winner_id,
                            metadata.get("first_publish_time"),
                            metadata.get("last_publish_time"),
                        ),
                    )

                    connection.executemany(
                        """
                        INSERT INTO runners(
                            market_id, selection_id, runner_name, sort_priority,
                            status, adjustment_factor
                        ) VALUES (?, ?, ?, ?, ?, ?)
                        """,
                        [
                            (
                                parsed["market_id"], r["selection_id"], r["runner_name"],
                                r["sort_priority"], r["status"], r["adjustment_factor"],
                            )
                            for r in parsed["runners"]
                        ],
                    )

                    connection.executemany(
                        """
                        INSERT OR IGNORE INTO price_history(
                            market_id, publish_time, selection_id, last_traded_price,
                            total_matched, best_back_price, best_back_size,
                            best_lay_price, best_lay_size, in_play, market_status
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """,
                        parsed["prices"],
                    )

                    connection.executemany(
                        """
                        INSERT OR REPLACE INTO settlements(
                            market_id, selection_id, runner_status, settled_at
                        ) VALUES (?, ?, ?, ?)
                        """,
                        [
                            (
                                parsed["market_id"], selection_id, status, settled_at
                            )
                            for selection_id, (status, settled_at)
                            in parsed["settlements"].items()
                        ],
                    )

                    if len(parsed["runners"]) != 3:
                        _log(
                            connection, import_id, "ERROR", "RUNNER_COUNT",
                            f"Expected 3 runners, found {len(parsed['runners'])}",
                            parsed["market_id"],
                        )
                    if not parsed["prices"]:
                        _log(
                            connection, import_id, "ERROR", "NO_PRICE_HISTORY",
                            "No runner price updates were found",
                            parsed["market_id"],
                        )
                    if not settled:
                        _log(
                            connection, import_id, "WARNING", "UNSETTLED",
                            "No settlement statuses found",
                            parsed["market_id"],
                        )

                    counts["markets_imported"] += 1
                    if counts["markets_imported"] % 10 == 0:
                        connection.commit()

                except Exception as exc:
                    counts["errors"] += 1
                    _log(
                        connection, import_id, "ERROR", "PARSE_FAILED",
                        f"{member.name}: {exc}",
                    )

            connection.execute(
                """
                UPDATE imports
                SET completed_at = CURRENT_TIMESTAMP,
                    status = 'completed',
                    files_scanned = ?,
                    markets_parsed = ?,
                    test_markets_found = ?,
                    markets_imported = ?,
                    duplicates_skipped = ?,
                    errors = ?
                WHERE id = ?
                """,
                (
                    counts["files_scanned"], counts["markets_parsed"],
                    counts["test_markets_found"], counts["markets_imported"],
                    counts["duplicates_skipped"], counts["errors"], import_id,
                ),
            )
            connection.commit()

        return {
            "status": "completed",
            "archive": archive_path.name,
            "import_id": import_id,
            **counts,
        }

    except Exception as exc:
        with database.connect() as connection:
            connection.execute(
                """
                UPDATE imports
                SET completed_at = CURRENT_TIMESTAMP, status = 'failed', notes = ?
                WHERE id = ?
                """,
                (str(exc), import_id),
            )
            connection.commit()
        raise
