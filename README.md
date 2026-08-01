# Betfair Research Lab v0.5

Version 0.5 adds the first **real SQLite importer** for Betfair historical
cricket data.

## What this version can do

- Scan Betfair `.tar` archives
- Open nested `.bz2` market streams
- Parse Betfair Stream API JSON
- Identify likely Test Match `MATCH_ODDS` markets
- Import market metadata, runners, price updates and settlements into SQLite
- Skip duplicate Betfair market IDs
- Log archive imports and integrity warnings
- Verify the database
- Show database totals and date coverage

## Install

Python 3.11 or newer is recommended.

```bash
python -m pip install -r requirements.txt
```

`orjson` is optional but recommended. The program falls back to Python's
built-in `json` module if it is unavailable.

## Commands

Create a database:

```bash
python cricket_research.py init cricket_research.sqlite
```

Scan an archive:

```bash
python cricket_research.py scan "C:\Betfair\data.tar"
```

Audit market metadata without importing:

```bash
python cricket_research.py audit "C:\Betfair\data.tar" --output audit.csv
```

Import Test Match Odds markets:

```bash
python cricket_research.py import "C:\Betfair\data.tar" --database cricket_research.sqlite
```

Show database totals:

```bash
python cricket_research.py stats --database cricket_research.sqlite
```

Verify integrity:

```bash
python cricket_research.py verify --database cricket_research.sqlite
```

## Test-match detection

Betfair historical files do not always expose a perfect "format = Test"
field. This release therefore combines:

- `marketType == MATCH_ODDS`
- exactly three runners
- one runner named `The Draw` or `Draw`
- event or competition text containing Test-match indicators
- exclusion rules for T20, ODI, domestic and other short formats

Anything uncertain is logged for review rather than silently treated as a
confirmed Test match.

## Important

This is the first importer release. Before using it for live-money research,
run `verify` and inspect `integrity_log`. The next release will improve
classification and add derived pre-match/price-path statistics.
