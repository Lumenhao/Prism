param(
    [switch]$OpenAnki,
    [switch]$Quiet
)

$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $PSScriptRoot
$configPath = Join-Path $root "config.json"
$cfg = Get-Content $configPath -Raw -Encoding UTF8 | ConvertFrom-Json
$script:url = $cfg.anki.url
$script:ankiExe = $cfg.system.anki_exe
if ($script:ankiExe) {
    $script:ankiExe = [Environment]::ExpandEnvironmentVariables($script:ankiExe)
    if ($script:ankiExe -match '^~[\\/](.*)$') {
        $script:ankiExe = Join-Path $HOME $Matches[1]
    }
}

function Invoke-Anki {
    param(
        [string]$Action,
        [hashtable]$Params = @{}
    )
    $body = @{ action = $Action; version = 6; params = $Params } | ConvertTo-Json -Depth 10
    Invoke-RestMethod -Uri $script:url -Method Post -Body $body -ContentType "application/json" -TimeoutSec 8
}

$connected = $false
for ($i = 0; $i -lt 2 -and -not $connected; $i++) {
    try {
        $null = Invoke-Anki "version"
        $connected = $true
    }
    catch {
        if ($i -eq 0 -and $script:ankiExe -and (Test-Path $script:ankiExe)) {
            Start-Process $script:ankiExe | Out-Null
            Start-Sleep -Seconds 7
        }
    }
}

if (-not $connected) {
    Write-Error "无法连接 AnkiConnect（$script:url）。请先打开 Anki 并安装 AnkiConnect。"
    exit 1
}

$decks = @(
    $cfg.anki.decks.vocab,
    $cfg.anki.decks.phrases,
    $cfg.anki.decks.listening
)

$stats = (Invoke-Anki "getDeckStats" @{ decks = $decks }).result
$new = 0
$learn = 0
$review = 0

if ($stats) {
    foreach ($prop in $stats.PSObject.Properties) {
        $s = $prop.Value
        $new += [int]$s.new_count
        $learn += [int]$s.learn_count
        $review += [int]$s.review_count
    }
}

$due = $new + $learn + $review
$message = "待复习 $due 张（新 $new / 学习中 $learn / 复习 $review）"

if ($due -gt 0) {
    if (-not $Quiet) {
        Add-Type -AssemblyName System.Windows.Forms
        Add-Type -AssemblyName System.Drawing
        $notify = New-Object System.Windows.Forms.NotifyIcon
        $notify.Icon = [System.Drawing.SystemIcons]::Information
        $notify.BalloonTipTitle = "PaperToTalk · 该复习了"
        $notify.BalloonTipText = $message
        $notify.Visible = $true
        $notify.ShowBalloonTip(10000)
        Start-Sleep -Seconds 2
        $notify.Dispose()
    }
    Write-Output $message
    if ($OpenAnki -and $script:ankiExe -and (Test-Path $script:ankiExe)) {
        Start-Process $script:ankiExe | Out-Null
    }
}
else {
    Write-Output "今天没有到期卡片。"
}
