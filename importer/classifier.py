from __future__ import annotations
from .common import DRAW_NAMES, NEGATIVE_TERMS, TEST_NATIONS, norm

def is_test_match(definition: dict) -> tuple[bool, str]:
    if definition.get("marketType") != "MATCH_ODDS":
        return False, "not MATCH_ODDS"
    if definition.get("name") not in {None, "Match Odds"}:
        return False, "market name is not Match Odds"

    runners = definition.get("runners", [])
    names = [norm(r.get("name")) for r in runners]
    if len(names) != 3 or not any(name in DRAW_NAMES for name in names):
        return False, "not a three-runner market with draw"

    teams = [name for name in names if name not in DRAW_NAMES]
    text = norm(" ".join(str(definition.get(k, "")) for k in ("eventName", "name")))
    competition = definition.get("competition")
    if isinstance(competition, dict):
        text += " " + norm(competition.get("name"))
    else:
        text += " " + norm(competition)

    if any(term in text for term in NEGATIVE_TERMS):
        return False, "short/domestic format keyword"
    if any(term in text for term in ("test", "ashes", "world test championship", "wtc")):
        return True, "explicit Test/Ashes/WTC wording"
    if len(teams) == 2 and all(team in TEST_NATIONS for team in teams):
        return True, "both runners are recognised Test nations"
    return False, "insufficient evidence of Test match"
