from __future__ import annotations

from typing import Any


def is_three_runner_match_odds(metadata: dict[str, Any]) -> bool:
    return (
        metadata.get("market_type") == "MATCH_ODDS"
        and metadata.get("runner_count") == 3
    )
