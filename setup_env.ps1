$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot

# Models, tools and caches live outside the repository. Set LUMEN_SUITE to move them.
$Suite = if ($env:LUMEN_SUITE) {
    $env:LUMEN_SUITE
} elseif (Test-Path "E:\") {
    "E:\LumenSuite"
} else {
    Join-Path $env:LOCALAPPDATA "LumenSuite"
}

$env:HF_HOME = Join-Path $Suite "models\hf"
$env:HF_ENDPOINT = "https://hf-mirror.com"
$env:HF_HUB_DISABLE_XET = "1"
$env:TORCH_HOME = Join-Path $Suite "models\torch"
$env:XDG_CACHE_HOME = Join-Path $Suite "cache"
$env:UV_CACHE_DIR = Join-Path $Suite "cache\uv"
$env:PIP_CACHE_DIR = Join-Path $Suite "cache\pip"
$env:UV_PYTHON_INSTALL_DIR = Join-Path $Suite "tools\python"

New-Item -ItemType Directory -Force -Path $env:HF_HOME, $env:TORCH_HOME, $env:XDG_CACHE_HOME, $env:UV_PYTHON_INSTALL_DIR | Out-Null

$python = Join-Path $PSScriptRoot ".venv\Scripts\python.exe"
$uv = Get-Command uv -ErrorAction SilentlyContinue
$py = Get-Command py -ErrorAction SilentlyContinue

if (-not (Test-Path $python)) {
    Write-Host "Creating .venv with Python 3.12 ..."
    if ($uv) {
        & uv venv --python 3.12 .venv
    } elseif ($py) {
        & py -3.12 -m venv .venv
    } else {
        throw "Python 3.12 was not found. Install it from https://www.python.org/downloads/ or install uv (https://docs.astral.sh/uv/), then run setup_env.ps1 again."
    }
}

if ($uv) {
    & uv pip install --python $python --index-url https://download.pytorch.org/whl/cpu torch
    & uv pip install --python $python -r requirements.txt
} else {
    & $python -m pip install --upgrade pip
    & $python -m pip install torch --index-url https://download.pytorch.org/whl/cpu
    & $python -m pip install -r requirements.txt
}

& $python -c "import fastapi, uvicorn, webview" 2>$null
if ($LASTEXITCODE -ne 0) {
    throw "Installation finished but the core packages could not be imported. Delete .venv and run setup_env.ps1 again."
}

Write-Host ""
Write-Host "Done. Start the workbench with:"
Write-Host "  .\Prism.bat"
Write-Host ""
Write-Host "Models and caches live under $Suite (override with LUMEN_SUITE)."
Write-Host "HuggingFace downloads use hf-mirror.com; no account is required."
