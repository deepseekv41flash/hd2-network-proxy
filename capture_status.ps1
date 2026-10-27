# capture_status.ps1 -- one-glance status of the capture run. ASCII-ONLY on purpose.
#
# Usage: powershell -ExecutionPolicy Bypass -File capture_status.ps1

$ErrorActionPreference = 'SilentlyContinue'
$root = "D:\Downloads\variant_mod"
$dump = "D:\mod\out\gwe"

Write-Host "=== session ==="
$rec = $null
if (Test-Path "$root\logs\pids.json") { $rec = Get-Content "$root\logs\pids.json" -Raw | ConvertFrom-Json }
if ($rec) {
    $pr = Get-Process -Id $rec.proxy
    if ($pr) { Write-Host "  proxy record : pid $($rec.proxy) alive, started $($rec.started)" }
    else { Write-Host "  proxy record : pid $($rec.proxy) DEAD (stale) -> run run_capture.ps1 again" }
} else {
    Write-Host "  proxy record : none (proxy not started)"
}
$listen = Get-NetTCPConnection -State Listen -LocalPort 443
if ($listen) {
    foreach ($l in $listen) { Write-Host "  listening    : $($l.LocalAddress):443  pid $($l.OwningProcess)" }
} else {
    Write-Host "  listening    : nothing on 443"
}

Write-Host "=== capture ==="
$idx = Join-Path $dump 'index.txt'
if (Test-Path $idx) {
    $lines = @(Get-Content $idx)
    Write-Host "  index.txt    : $($lines.Count) response(s)"
    $lines | Select-Object -Last 6 | ForEach-Object { Write-Host "    $_" }
} else {
    Write-Host "  index.txt    : not yet (no response matched the whitelist)"
}
$files = @(Get-ChildItem $dump -Filter *.json)
Write-Host "  json bodies  : $($files.Count)"
$files | Sort-Object Length -Descending | Select-Object -First 5 |
    ForEach-Object { Write-Host ("    {0,-52} {1,9:N0} B" -f $_.Name, $_.Length) }

Write-Host "=== proxy.log (last 8) ==="
Get-Content "$root\logs\proxy.log" -Tail 8 | ForEach-Object { Write-Host "  $_" }

Write-Host ""
Write-Host "=== next ==="
if (-not (Test-Path $idx)) {
    Write-Host "  launch the game: log in -> ship -> open map -> switch planet once"
    Write-Host "  if proxy.log shows no request at all after that, the client never reached us"
    Write-Host "  (check WinINET proxy / HTTP_PROXY env vars / TUN mode)"
} else {
    Write-Host "  capture has data: tell the assistant, then run stop.ps1"
}
