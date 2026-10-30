@echo off
setlocal
cd /d "%~dp0"
title Prism

if not exist ".venv\Scripts\python.exe" (
  echo.
  echo   Prism is setting itself up for the first run.
  echo   Python packages total roughly 1.5 GB and are kept outside this folder.
  echo   This can take 5-15 minutes; the window stays open until it finishes.
  echo.
  powershell -NoProfile -ExecutionPolicy Bypass -File "setup_env.ps1"
  if errorlevel 1 goto failed
)

if not exist ".venv\Scripts\python.exe" goto failed

set PRISM_HIDE_CONSOLE=1
".venv\Scripts\python.exe" "app\launch.py"
if errorlevel 1 (
  echo.
  echo Prism exited with an error. See data\launch.log for details.
  pause
)
exit /b 0

:failed
echo.
echo Setup did not finish. Check the messages above, then run setup_env.ps1 again.
pause
exit /b 1
