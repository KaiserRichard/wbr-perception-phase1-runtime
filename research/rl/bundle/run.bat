@echo off
setlocal
echo G1: smoke, pilot, then parallel seeds and evaluation. Default min(5, CPU threads/2) jobs.
echo Usage: run.bat [--jobs N] [--seed-wall-cap-min MINUTES]  ^(default: unlimited^).
cd /d "%~dp0"
"%~dp0python\python.exe" "%~dp0launch.py" run %*
set "RESULT=%ERRORLEVEL%"
echo Exit code: %RESULT%. Keep this window and the USB connected until verified.
pause
exit /b %RESULT%
