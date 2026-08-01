@echo off
if "%~1"=="" (
  echo Drag a Betfair .tar file onto this file.
  pause
  exit /b 1
)
python cricket_research.py import "%~1" --database cricket_research.sqlite
pause
