@echo off
setlocal
cd /d "%~dp0"
:menu
cls
echo ========================================
echo       Betfair Cricket Research v1.0
echo ========================================
echo.
echo 1. Install requirements (first time only)
echo 2. Import a Betfair TAR archive
echo 3. Show database statistics
echo 4. Verify database
echo 5. Build match summaries
echo 6. Export summary for ChatGPT
echo 7. Exit
echo.
set /p choice=Choose 1-7: 
if "%choice%"=="1" goto install
if "%choice%"=="2" goto import
if "%choice%"=="3" goto stats
if "%choice%"=="4" goto verify
if "%choice%"=="5" goto derive
if "%choice%"=="6" goto export
if "%choice%"=="7" exit /b 0
goto menu
:install
python -m pip install -r requirements.txt
pause
goto menu
:import
set /p archive=Paste the full path to the .tar file: 
python cricket_research.py import "%archive%" --database cricket_research.sqlite
if errorlevel 1 goto paused
python cricket_research.py derive --database cricket_research.sqlite
python cricket_research.py verify --database cricket_research.sqlite
:paused
pause
goto menu
:stats
python cricket_research.py stats --database cricket_research.sqlite
pause
goto menu
:verify
python cricket_research.py verify --database cricket_research.sqlite
pause
goto menu
:derive
python cricket_research.py derive --database cricket_research.sqlite
pause
goto menu
:export
python cricket_research.py derive --database cricket_research.sqlite
python cricket_research.py export cricket_research_summary.csv --database cricket_research.sqlite
pause
goto menu
