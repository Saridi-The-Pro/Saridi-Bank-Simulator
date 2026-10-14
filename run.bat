@echo off
cd /d "%~dp0"

python bank.py
if errorlevel 1 (
  echo.
  echo The program exited with an error.
)

pause