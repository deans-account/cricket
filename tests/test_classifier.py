from importer.classifier import is_test_match


def test_explicit_test():
    md = {
        "marketType": "MATCH_ODDS",
        "name": "Match Odds",
        "eventName": "England v India - 1st Test",
        "runners": [
            {"name": "England"}, {"name": "India"}, {"name": "The Draw"}
        ],
    }
    assert is_test_match(md)[0]


def test_test_nations_without_test_word():
    md = {
        "marketType": "MATCH_ODDS",
        "name": "Match Odds",
        "eventName": "Australia v Pakistan",
        "runners": [
            {"name": "Australia"}, {"name": "Pakistan"}, {"name": "The Draw"}
        ],
    }
    assert is_test_match(md)[0]


def test_reject_t20():
    md = {
        "marketType": "MATCH_ODDS",
        "name": "Match Odds",
        "eventName": "England v India 1st T20I",
        "runners": [
            {"name": "England"}, {"name": "India"}, {"name": "The Draw"}
        ],
    }
    assert not is_test_match(md)[0]
