from __future__ import annotations

import re
from typing import Any


TEST_POSITIVE_PATTERNS = [
    r"\btest\b",
    r"\btests\b",
    r"\bashes\b",
    r"world test championship",
    r"\bw?tc\b",
]

TEST_NEGATIVE_PATTERNS = [
    r"\bt20\b",
    r"\bt20i\b",
    r"\bone day\b",
    r"\bodi\b",
    r"\bhundred\b",
    r"\bbig bash\b",
    r"\bipl\b",
    r"\bblast\b",
    r"\bcounty championship\b",
    r"\bsheffield shield\b",
    r"\branji\b",
    r"\bfirst class\b",
    r"\bwomen'?s? premier league\b",
]


def _text(metadata: dict[str, Any]) -> str:
    parts = [
        metadata.get("event_name"),
        metadata.get("market_name"),
        metadata.get("competition"),
    ]
    return " ".join(str(p) for p in parts if p).lower()


def classify_test_match(metadata: dict[str, Any]) -> tuple[str, str]:
    if metadata.get("market_type") != "MATCH_ODDS":
        return "excluded", "market_type is not MATCH_ODDS"

    runner_names = [str(x).strip().lower() for x in metadata.get("runner_names", [])]
    if len(runner_names) != 3:
        return "excluded", f"runner_count={len(runner_names)} instead of 3"

    if not any(name in {"the draw", "draw"} for name in runner_names):
        return "excluded", "three-runner market has no draw runner"

    text = _text(metadata)

    for pattern in TEST_NEGATIVE_PATTERNS:
        if re.search(pattern, text, flags=re.IGNORECASE):
            return "excluded", f"negative format pattern: {pattern}"

    for pattern in TEST_POSITIVE_PATTERNS:
        if re.search(pattern, text, flags=re.IGNORECASE):
            return "confirmed_test", f"positive Test pattern: {pattern}"

    # Three-runner cricket match odds with a draw but no explicit format marker.
    return "uncertain_test", "three-runner MATCH_ODDS with draw, no explicit Test marker"
