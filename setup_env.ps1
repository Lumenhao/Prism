$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot

$Suite = if ($env:LUMEN_SUITE) { $env:LUMEN_SUITE } else { "E:\LumenSuite" }
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

if (-not (Test-Path $python)) {
    Write-Host "Creating .venv with Python 3.12 ..."
    if (Get-Command uv -ErrorAction SilentlyContinue) {
        uv venv --python 3.12 .venv
    } else {
        py -3.12 -m venv .venv
    }
}

if (Get-Command uv -ErrorAction SilentlyContinue) {
    uv pip install --python $python --index-url https://download.pytorch.org/whl/cpu torch
    uv pip install --python $python -r requirements.txt
} else {
    & $python -m pip install --upgrade pip
    & $python -m pip install torch --index-url https://download.pytorch.org/whl/cpu
    & $python -m pip install -r requirements.txt
}

Write-Host ""
Write-Host "Done. Start the workbench with:"
Write-Host "  .\Prism.bat"
Write-Host ""
Write-Host "Models and caches live under $Suite. HuggingFace downloads use hf-mirror.com."
