# Betfair Research Lab v0.7

This is the first complete Test Match Odds importer release.

## What it does

- Opens Betfair `.tar` archives containing `.bz2` historical market streams.
- Ignores archive folder names and reads Betfair market metadata.
- Keeps only three-runner `MATCH_ODDS` markets with a Draw.
- Identifies Test matches from explicit Test wording or recognised Test nations.
- Imports markets, runners, price history, best available prices and settlements.
- Prevents duplicate archives using SHA-256.
- Prevents duplicate Betfair market IDs and duplicate team/date match keys.
- Logs corrupt files, missing prices and missing settlements.
- Reports exactly which years and months are in the database.
- Runs database integrity checks.

## Windows setup

1. Install Python 3.11 or newer from python.org.
2. During installation tick **Add Python to PATH**.
3. Extract this project ZIP.
4. Double-click `install_requirements.bat`.

## Import an archive

Drag a Betfair `.tar` file onto `import_archive.bat`.

The program creates or updates:

`cricket_research.sqlite`

You can import further archives the same way. Existing data is preserved and duplicates are skipped.

## Check the database

Double-click:

- `database_stats.bat`
- `verify_database.bat`

## Command-line alternatives

```bat
python cricket_research.py import "C:\Betfair\data.tar" --database cricket_research.sqlite
python cricket_research.py stats --database cricket_research.sqlite
python cricket_research.py verify --database cricket_research.sqlite
```

## Note

This release is for building and validating the historical database. Strategy optimisation is the next stage after the imported data has been checked.
