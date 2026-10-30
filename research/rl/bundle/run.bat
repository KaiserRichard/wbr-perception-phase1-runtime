@echo off
setlocal
cd /d "%~dp0"
"%~dp0python\python.exe" "%~dp0launch.py" run %*
set "RESULT=%ERRORLEVEL%"
echo Exit code: %RESULT%. Keep this window and the USB connected until verified.
pause
exit /b %RESULT%
