# ============================================================
# Daily Inquiry Log — ファイアウォール開放スクリプト
# 右クリック → "管理者として実行" してください
# ============================================================
#Requires -RunAsAdministrator

$port = 4173
$ruleName = "Daily-Inquiry-Log-Port-$port"

Write-Host ""
Write-Host "=== Daily Inquiry Log ファイアウォール設定 ===" -ForegroundColor Cyan
Write-Host ""

$existing = Get-NetFirewallRule -DisplayName $ruleName -ErrorAction SilentlyContinue
if ($existing) {
    Write-Host "ルールは既に存在します: $ruleName" -ForegroundColor Green
} else {
    Write-Host "ポート $port のファイアウォールルールを追加中..." -ForegroundColor Yellow
    New-NetFirewallRule `
        -DisplayName $ruleName `
        -Direction Inbound `
        -Protocol TCP `
        -LocalPort $port `
        -Action Allow `
        -Profile Private `
        -Description "Daily Inquiry Log web app" | Out-Null
    Write-Host "追加しました: $ruleName" -ForegroundColor Green
}

Write-Host ""
Write-Host "PCのIPアドレス:" -ForegroundColor Cyan
Get-NetIPAddress -AddressFamily IPv4 |
    Where-Object { $_.InterfaceAlias -notmatch 'Loopback' -and $_.IPAddress -notmatch '^169\.' } |
    Select-Object InterfaceAlias, IPAddress |
    Format-Table -AutoSize

Write-Host "スマホのブラウザで上記IPアドレスを使って:" -ForegroundColor Cyan
Write-Host "  http://<IPアドレス>:$port/" -ForegroundColor White
Write-Host ""
Read-Host "Enterで終了"
