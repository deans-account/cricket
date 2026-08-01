from importer.market_filter import is_three_runner_match_odds


def test_three_runner_match_odds():
    assert is_three_runner_match_odds({
        "market_type": "MATCH_ODDS",
        "runner_count": 3,
    })


def test_reject_other_market():
    assert not is_three_runner_match_odds({
        "market_type": "TO_WIN_THE_TOSS",
        "runner_count": 2,
    })
