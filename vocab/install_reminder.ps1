[CmdletBinding()]
param(
    [string]$Time = "20:30",
    [string]$TaskName = "PaperToTalk Review",
    [switch]$OpenAnki,
    [switch]$Uninstall
)

$ErrorActionPreference = "Stop"
$remind = Join-Path $PSScriptRoot "remind.ps1"
$currentUser = [System.Security.Principal.WindowsIdentity]::GetCurrent().Name

function Remove-ReviewTask {
    try {
        Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false -ErrorAction Stop
        Write-Output "已删除计划任务：$TaskName"
        return
    }
    catch {
        $null = schtasks.exe /Delete /TN $TaskName /F 2>&1
        if ($LASTEXITCODE -eq 0) {
            Write-Output "已删除计划任务：$TaskName"
            return
        }
        throw "没有找到计划任务「$TaskName」，或删除失败。"
    }
}

if ($Uninstall) {
    Remove-ReviewTask
    return
}

if (-not (Test-Path $remind)) {
    throw "找不到 $remind，请在仓库的 vocab/ 目录下运行本脚本。"
}

if ($Time -notmatch '^([01]\d|2[0-3]):[0-5]\d$') {
    throw "时间格式应为 HH:mm（24 小时制），例如 20:30。"
}

$arguments = "-NoProfile -ExecutionPolicy Bypass -WindowStyle Hidden -File `"$remind`""
if ($OpenAnki) {
    $arguments += " -OpenAnki"
}

$action = New-ScheduledTaskAction -Execute "powershell.exe" -Argument $arguments
$trigger = New-ScheduledTaskTrigger -Daily -At $Time
$settings = New-ScheduledTaskSettingsSet `
    -StartWhenAvailable `
    -AllowStartIfOnBatteries `
    -DontStopIfGoingOnBatteries `
    -ExecutionTimeLimit (New-TimeSpan -Minutes 5)

$registered = $false
try {
    $principal = New-ScheduledTaskPrincipal -UserId $currentUser -LogonType Interactive -RunLevel Limited
    Register-ScheduledTask `
        -TaskName $TaskName `
        -Action $action `
        -Trigger $trigger `
        -Settings $settings `
        -Principal $principal `
        -Description "PaperToTalk 每日 Anki 复习提醒" `
        -Force | Out-Null
    $registered = $true
}
catch {
    # 旧系统或受限账户回退到 schtasks；任务只会在当前用户登录时运行。
    $null = schtasks.exe /Create /SC DAILY /TN $TaskName /TR $arguments /ST $Time /F 2>&1
    if ($LASTEXITCODE -eq 0) {
        $registered = $true
    }
}

if (-not $registered) {
    throw "注册计划任务失败。可手动运行：schtasks /Create /SC DAILY /TN `"$TaskName`" /TR `"$arguments`" /ST $Time /F"
}

Write-Output "已注册计划任务：$TaskName"
Write-Output "时间：每天 $Time（仅在你登录时运行）"
Write-Output "命令：powershell.exe $arguments"
Write-Output "立即测试：powershell -NoProfile -ExecutionPolicy Bypass -File `"$remind`""
Write-Output "删除提醒：powershell -NoProfile -ExecutionPolicy Bypass -File `"$PSCommandPath`" -Uninstall"
