from __future__ import annotations

import bz2
import csv
import io
import json
import tarfile
from collections import Counter
from pathlib import Path
from typing import Any, Iterable, Iterator

try:
    import orjson

    def loads_json(value: bytes) -> Any:
        return orjson.loads(value)
except ImportError:
    def loads_json(value: bytes) -> Any:
        return json.loads(value)


def iter_messages(raw_bz2: bytes) -> Iterator[dict[str, Any]]:
    with bz2.BZ2File(io.BytesIO(raw_bz2), "rb") as stream:
        for raw_line in stream:
            if raw_line.strip():
                yield loads_json(raw_line)


def extract_market_definition(messages: Iterable[dict[str, Any]]) -> tuple[str | None, dict[str, Any] | None, int | None]:
    first_publish_time = None
    for message in messages:
        if first_publish_time is None:
            first_publish_time = message.get("pt")
        if message.get("op") != "mcm":
            continue
        for change in message.get("mc", []):
            definition = change.get("marketDefinition")
            if definition:
                return change.get("id"), definition, first_publish_time
    return None, None, first_publish_time


def metadata_from_definition(
    market_id: str | None,
    definition: dict[str, Any],
    source_file: str,
    publish_time: int | None,
) -> dict[str, Any]:
    competition = definition.get("competition")
    competition_name = competition.get("name") if isinstance(competition, dict) else competition
    runners = definition.get("runners", [])

    return {
        "source_file": source_file,
        "market_id": market_id,
        "event_name": definition.get("eventName"),
        "market_name": definition.get("name"),
        "market_type": definition.get("marketType"),
        "market_time": definition.get("marketTime"),
        "event_type_id": definition.get("eventTypeId"),
        "competition": competition_name,
        "country_code": definition.get("countryCode"),
        "timezone": definition.get("timezone"),
        "number_of_winners": definition.get("numberOfWinners"),
        "runner_count": len(runners),
        "runner_names": [r.get("name") for r in runners if r.get("name")],
        "status": definition.get("status"),
        "in_play": definition.get("inPlay"),
        "publish_time": publish_time,
    }


def parse_market_metadata(raw_bz2: bytes, source_name: str) -> dict[str, Any]:
    market_id, definition, publish_time = extract_market_definition(iter_messages(raw_bz2))
    if definition is None:
        raise ValueError("No marketDefinition found")
    return metadata_from_definition(market_id, definition, source_name, publish_time)


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
                errors.append({"source_file": member.name, "error": "Could not extract"})
                continue
            try:
                metadata = parse_market_metadata(extracted.read(), member.name)
                markets.append(metadata)
                if metadata.get("market_type"):
                    market_types[str(metadata["market_type"])] += 1
                market_time = metadata.get("market_time")
                if isinstance(market_time, str) and len(market_time) >= 4:
                    event_years[market_time[:4]] += 1
            except Exception as exc:
                errors.append({"source_file": member.name, "error": str(exc)})

    return {
        "summary": {
            "archive": path.name,
            "bz2_files_scanned": scanned,
            "markets_parsed": len(markets),
            "errors": len(errors),
            "market_types": dict(market_types.most_common()),
            "event_years": dict(sorted(event_years.items())),
        },
        "markets": markets,
        "errors": errors,
    }


def write_audit(markets: Iterable[dict[str, Any]], output_path: Path) -> None:
    rows = list(markets)
    if output_path.suffix.lower() == ".json":
        output_path.write_text(json.dumps(rows, indent=2), encoding="utf-8")
        return
    if output_path.suffix.lower() != ".csv":
        raise ValueError("Output must end in .csv or .json")

    fieldnames = [
        "source_file", "market_id", "event_name", "market_name", "market_type",
        "market_time", "event_type_id", "competition", "country_code", "timezone",
        "number_of_winners", "runner_count", "runner_names", "status", "in_play",
        "publish_time",
    ]
    with output_path.open("w", newline="", encoding="utf-8-sig") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            clean = dict(row)
            clean["runner_names"] = " | ".join(clean.get("runner_names", []))
            writer.writerow(clean)
