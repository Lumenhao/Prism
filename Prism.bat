@echo off
setlocal
cd /d "%~dp0"
if not exist ".venv\Scripts\pythonw.exe" (
  echo Prism needs its Python environment first.
  echo Run:  setup_env.ps1
  pause
  exit /b 1
)
start "" ".venv\Scripts\pythonw.exe" "app\launch.py"
