@echo off
setlocal
cd /d "%~dp0"
if "%~1"=="" (
  echo Drag a Betfair .tar file onto this file.
  pause
  exit /b 1
)
python cricket_research.py import "%~1" --database cricket_research.sqlite
if errorlevel 1 (
  echo Import failed. See the message above.
  pause
  exit /b 1
)
python cricket_research.py derive --database cricket_research.sqlite
python cricket_research.py verify --database cricket_research.sqlite
python cricket_research.py stats --database cricket_research.sqlite
pause
