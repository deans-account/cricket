@echo off
python cricket_research.py derive --database cricket_research.sqlite
python cricket_research.py export cricket_research_summary.csv --database cricket_research.sqlite
pause
