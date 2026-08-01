from __future__ import annotations

import bz2
import csv
import io
import json
import tarfile
from collections import Counter
from pathlib import Path
from typing import Any, Iterable

try:
    import orjson

    def loads_json(value: bytes) -> Any:
        return orjson.loads(value)
except ImportError:
    def loads_json(value: bytes) -> Any:
        return json.loads(value)


def _first_market_definition(message: dict[str, Any]) -> tuple[str | None, dict[str, Any] | None]:
    if message.get("op") != "mcm":
        return None, None

    for market_change in message.get("mc", []):
        market_id = market_change.get("id")
        definition = market_change.get("marketDefinition")
        if definition:
            return market_id, definition
    return None, None


def _runner_names(definition: dict[str, Any]) -> list[str]:
    names: list[str] = []
    for runner in definition.get("runners", []):
        name = runner.get("name")
        if name:
            names.append(str(name))
    return names


def parse_market_file(raw_bz2: bytes, source_name: str) -> dict[str, Any]:
    market_id: str | None = None
    definition: dict[str, Any] | None = None
    publish_time: int | None = None
    line_count = 0

    with bz2.BZ2File(io.BytesIO(raw_bz2), "rb") as stream:
        for raw_line in stream:
            line_count += 1
            if not raw_line.strip():
                continue
            message = loads_json(raw_line)
            if publish_time is None:
                publish_time = message.get("pt")
            candidate_id, candidate_definition = _first_market_definition(message)
            if candidate_definition:
                market_id = candidate_id
                definition = candidate_definition
                break

    if definition is None:
        raise ValueError("No marketDefinition found")

    event_name = definition.get("eventName")
    market_type = definition.get("marketType")
    market_time = definition.get("marketTime")
    competition = definition.get("competition")
    if isinstance(competition, dict):
        competition_name = competition.get("name")
    else:
        competition_name = competition

    return {
        "source_file": source_name,
        "market_id": market_id,
        "event_name": event_name,
        "market_name": definition.get("name"),
        "market_type": market_type,
        "market_time": market_time,
        "event_type_id": definition.get("eventTypeId"),
        "competition": competition_name,
        "country_code": definition.get("countryCode"),
        "timezone": definition.get("timezone"),
        "number_of_winners": definition.get("numberOfWinners"),
        "runner_count": len(definition.get("runners", [])),
        "runner_names": _runner_names(definition),
        "status": definition.get("status"),
        "in_play": definition.get("inPlay"),
        "publish_time": publish_time,
        "lines_read": line_count,
    }


def audit_archive(archive_path: str | Path, limit: int | None = None) -> dict[str, Any]:
    path = Path(archive_path)
    markets: list[dict[str, Any]] = []
    errors: list[dict[str, str]] = []
    market_types: Counter[str] = Counter()
    event_years: Counter[str] = Counter()

    scanned = 0
    with tarfile.open(path, "r:*") as archive:
        for member in archive:
            if not member.isfile() or not member.name.lower().endswith(".bz2"):
                continue
            if limit is not None and scanned >= limit:
                break

            scanned += 1
            extracted = archive.extractfile(member)
            if extracted is None:
                errors.append({"source_file": member.name, "error": "Could not extract member"})
                continue

            try:
                metadata = parse_market_file(extracted.read(), member.name)
                markets.append(metadata)

                market_type = metadata.get("market_type")
                if market_type:
                    market_types[str(market_type)] += 1

                market_time = metadata.get("market_time")
                if isinstance(market_time, str) and len(market_time) >= 4:
                    event_years[market_time[:4]] += 1
            except Exception as exc:
                errors.append({"source_file": member.name, "error": str(exc)})

    summary = {
        "archive": path.name,
        "bz2_files_scanned": scanned,
        "markets_parsed": len(markets),
        "errors": len(errors),
        "market_types": dict(market_types.most_common()),
        "event_years": dict(sorted(event_years.items())),
    }

    return {"summary": summary, "markets": markets, "errors": errors}


def write_audit(markets: Iterable[dict[str, Any]], output_path: Path) -> None:
    rows = list(markets)
    suffix = output_path.suffix.lower()

    if suffix == ".json":
        output_path.write_text(json.dumps(rows, indent=2), encoding="utf-8")
        return

    if suffix != ".csv":
        raise ValueError("Output file must end in .csv or .json")

    fieldnames = [
        "source_file",
        "market_id",
        "event_name",
        "market_name",
        "market_type",
        "market_time",
        "event_type_id",
        "competition",
        "country_code",
        "timezone",
        "number_of_winners",
        "runner_count",
        "runner_names",
        "status",
        "in_play",
        "publish_time",
        "lines_read",
    ]

    with output_path.open("w", newline="", encoding="utf-8-sig") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            clean = dict(row)
            clean["runner_names"] = " | ".join(clean.get("runner_names", []))
            writer.writerow(clean)
