# Betfair Cricket Research v1.0

A usable Windows importer for Betfair Basic historical cricket archives.

## What v1.0 does

- Imports Betfair `.tar` archives containing `.bz2` stream files.
- Keeps Test Match `MATCH_ODDS` markets only.
- Stores runners, timestamped prices, available best back/lay prices and settlement results in SQLite.
- Prevents duplicate archives, market IDs and team/date match keys.
- Builds one-row-per-match research summaries.
- Checks the database for duplicates, missing runners, missing prices and SQLite corruption.
- Exports a compact CSV for analysis in ChatGPT.

## First-time setup on Windows

1. Install Python 3.11 or later from python.org.
2. During installation, tick **Add Python to PATH**.
3. Download and extract this project.
4. Double-click `install_requirements.bat` once.

## Normal use

### Import an archive

Drag a Betfair `.tar` file onto `import_archive.bat`.

The program creates or updates:

`cricket_research.sqlite`

After importing, it automatically builds match summaries and verifies the database.

### View totals and coverage

Double-click `database_stats.bat`.

### Verify the database

Double-click `verify_database.bat`.

### Export for ChatGPT

Double-click `export_for_chatgpt.bat`.

This creates:

`cricket_research_summary.csv`

Upload either the SQLite database or the CSV to ChatGPT for strategy analysis.

## Command-line use

```bat
python cricket_research.py import "C:\Betfair\data.tar" --database cricket_research.sqlite
python cricket_research.py derive --database cricket_research.sqlite
python cricket_research.py verify --database cricket_research.sqlite
python cricket_research.py stats --database cricket_research.sqlite
python cricket_research.py export cricket_research_summary.csv --database cricket_research.sqlite
```

## Data-quality note

Classification uses market metadata, not archive folder names. A Test market must be `MATCH_ODDS`, have exactly two teams plus a draw, and either contain explicit Test wording or involve recognised Test nations without short-format indicators. Review `integrity_log` for unsettled markets or parser errors.
