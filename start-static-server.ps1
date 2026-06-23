# ============================================================
# Daily Inquiry Log — 起動スクリプト
# ファイアウォール設定 + サーバー起動
# ============================================================
$ErrorActionPreference = "Stop"
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Definition
$nodePath = "C:\Program Files\nodejs\node.exe"
$port = 4173
$ruleName = "Daily-Inquiry-Log-Port-$port"

Write-Host ""
Write-Host "=== Daily Inquiry Log ===" -ForegroundColor Cyan

# --- ファイアウォール設定 ---
$isAdmin = ([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)

if ($isAdmin) {
    $rule = Get-NetFirewallRule -DisplayName $ruleName -ErrorAction SilentlyContinue
    if (-not $rule) {
        Write-Host "ファイアウォールルールを追加中..." -ForegroundColor Yellow
        New-NetFirewallRule `
            -DisplayName $ruleName `
            -Direction Inbound `
            -Protocol TCP `
            -LocalPort $port `
            -Action Allow `
            -Profile Private `
            -Description "Daily Inquiry Log web app" | Out-Null
        Write-Host "ファイアウォール: 設定完了" -ForegroundColor Green
    } else {
        Write-Host "ファイアウォール: 設定済み" -ForegroundColor Green
    }
} else {
    Write-Host "注意: 管理者権限がないため、ファイアウォールをスキップ" -ForegroundColor Yellow
    Write-Host "      スマホからアクセスできない場合は open-firewall.ps1 を管理者実行" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "サーバーを起動中..." -ForegroundColor Cyan
Write-Host ""
Set-Location -LiteralPath $scriptDir
& $nodePath serve-dist.mjs
