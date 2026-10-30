@echo off
setlocal
cd /d "%~dp0"
"%~dp0python\python.exe" "%~dp0launch.py" resume %*
set "RESULT=%ERRORLEVEL%"
echo Exit code: %RESULT%. Check runs for checkpoint and resume receipts.
pause
exit /b %RESULT%
