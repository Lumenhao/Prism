@echo off
setlocal
cd /d "%~dp0"
if not exist ".venv\Scripts\python.exe" (
  echo Prism needs its Python environment first.
  echo Run:  setup_env.ps1
  pause
  exit /b 1
)
set PRISM_HIDE_CONSOLE=1
".venv\Scripts\python.exe" "app\launch.py"
