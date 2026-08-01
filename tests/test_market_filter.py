from importer.market_filter import classify_test_match


def test_confirmed_test():
    result, _ = classify_test_match({
        "market_type": "MATCH_ODDS",
        "runner_names": ["England", "India", "The Draw"],
        "event_name": "England v India - 1st Test",
        "market_name": "Match Odds",
        "competition": "India in England",
    })
    assert result == "confirmed_test"


def test_reject_t20():
    result, _ = classify_test_match({
        "market_type": "MATCH_ODDS",
        "runner_names": ["England", "India", "The Draw"],
        "event_name": "England v India - 1st T20I",
        "market_name": "Match Odds",
        "competition": "T20 International",
    })
    assert result == "excluded"


def test_uncertain_three_runner():
    result, _ = classify_test_match({
        "market_type": "MATCH_ODDS",
        "runner_names": ["England", "India", "The Draw"],
        "event_name": "England v India",
        "market_name": "Match Odds",
        "competition": "India in England",
    })
    assert result == "uncertain_test"
