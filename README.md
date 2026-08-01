# Betfair Research Lab v0.8

Version 0.8 keeps the working v0.7 importer and adds a compact research layer.

## Current workflow

1. Install Python 3.11+ and tick **Add Python to PATH**.
2. Double-click `install_requirements.bat` once.
3. Drag a Betfair `.tar` archive onto `import_archive.bat`.
4. Double-click `verify_database.bat`.
5. Double-click `build_summaries.bat`.
6. Double-click `export_for_chatgpt.bat` to create
   `cricket_research_summary.csv`.

## New in v0.8

- `market_summary` table: one compact row per Test market.
- Correct pre-play price selection using the first in-play timestamp.
- Minimum/maximum traded prices for home, away and draw.
- Winner role and price-row counts.
- `derive` command to rebuild summaries.
- `export` command and one-click ChatGPT export.

## Commands

```bat
python cricket_research.py import "C:\Betfair\data.tar" --database cricket_research.sqlite
python cricket_research.py verify --database cricket_research.sqlite
python cricket_research.py derive --database cricket_research.sqlite
python cricket_research.py export cricket_research_summary.csv --database cricket_research.sqlite
```

The full SQLite database remains on your PC. The compact CSV is easier to
upload here for initial analysis; the SQLite file can still be uploaded when
full price-path testing is needed.
