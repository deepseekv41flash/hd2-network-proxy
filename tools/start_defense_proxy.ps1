# start_defense_proxy.ps1 -- start the third-party war_proxy in "defense campaign rewrite" mode.
# ASCII-only on purpose: Windows PowerShell 5.1 misreads UTF-8 without BOM and breaks on CJK quotes.
#
# Usage (spec = single-line JSON produced by defense_inject.py spec):
#   powershell -NoProfile -ExecutionPolicy Bypass -File tools\start_defense_proxy.ps1 `
#       -SpecFile D:\mod\work\variant-net\out\defense_spec_20261101.json
#
# Steps (idempotent, every file backed up):
#   1. stop the running proxy (stop.ps1), wait for :443 to be free
#   2. back up config.json / runtime\selection.json / runtime\status.json
#   3. write config-defense.json (targets=[], passthrough=false) + selection.json (enabled=false)
#   4. start proxy with HD2_GWE_EXTRA / HD2_GWE_DUMP / HD2_GWE_PATHS / HD2_GWE_REQ_PATHS
#
# Rollback: stop.ps1, then restore *.bak-defense-<stamp> (docs\DEFENSE-FORGE-RECIPE.md sec.5)
param(
    [Parameter(Mandatory=$true)][string]$SpecFile,
    [string]$Root     = 'D:\Downloads\variant_mod',
    [string]$Dump     = 'D:\mod\out\gwe',
    [string]$Paths    = '/api/WarSeason/801/Status,/api/Operation',
    [string]$ReqPaths = '/api/Operation'
)
$ErrorActionPreference = 'Stop'
function Step($m) { Write-Host ("[defense] " + $m) }

$spec = (Get-Content -LiteralPath $SpecFile -Raw).Trim()
if (-not $spec.StartsWith('{')) { throw "spec file is not JSON: $SpecFile" }
$spec | ConvertFrom-Json | Out-Null

# 1) stop old proxy
if (Test-Path (Join-Path $Root 'stop.ps1')) {
    Step "stopping old proxy"
    & (Join-Path $Root 'stop.ps1') 2>&1 | ForEach-Object { Write-Host ("[stop] " + $_) }
}
for ($i = 0; $i -lt 20; $i++) {
    if (-not (netstat -ano | Select-String ':443\s+.*LISTENING')) { break }
    Start-Sleep -Milliseconds 500
}
if (netstat -ano | Select-String ':443\s+.*LISTENING') { throw "port 443 still busy, aborting" }

# 2) backups
$stamp = Get-Date -Format 'yyyyMMdd-HHmmss'
foreach ($rel in @('config.json', 'runtime\selection.json', 'runtime\status.json')) {
    $src = Join-Path $Root $rel
    if (Test-Path $src) {
        Copy-Item -LiteralPath $src -Destination ($src + ".bak-defense-" + $stamp) -Force
        Step ("backup " + $rel + ".bak-defense-" + $stamp)
    }
}

# 3) clean config: no variant entries, rewrite path enabled
$cfg = Get-Content (Join-Path $Root 'config.json') -Raw | ConvertFrom-Json
$cfg.targets = @()
$cfg.passthrough = $false
$cfg | ConvertTo-Json -Depth 6 | Set-Content (Join-Path $Root 'config-defense.json') -Encoding UTF8
'{"enabled": false, "variants": [], "updated": "' + ((Get-Date).ToString('s')) + '"}' |
    Set-Content (Join-Path $Root 'runtime\selection.json') -Encoding UTF8
Step "wrote config-defense.json (targets=[], passthrough=false) + selection.json (enabled=false)"

# 4) start with env vars
$env:HD2_GWE_EXTRA     = $spec
$env:HD2_GWE_DUMP      = $Dump
$env:HD2_GWE_PATHS     = $Paths
$env:HD2_GWE_REQ_PATHS = $ReqPaths
$argList = @(
    (Join-Path $Root 'tools\war_proxy.py'),
    '--config',   (Join-Path $Root 'config-defense.json'),
    '--catalog',  (Join-Path $Root 'variant_catalog.json'),
    '--cert-dir', (Join-Path $Root 'certs')
)
$p = Start-Process -FilePath 'py' -ArgumentList $argList -WorkingDirectory $Root -WindowStyle Hidden -PassThru
@{ proxy = $p.Id; started = (Get-Date).ToString('s'); mode = 'defense'; spec = $spec } |
    ConvertTo-Json -Depth 3 | Set-Content (Join-Path $Root 'logs\pids.json') -Encoding UTF8
Start-Sleep -Seconds 3
if (-not (Get-Process -Id $p.Id -ErrorAction SilentlyContinue)) { throw "proxy exited immediately, see logs\proxy.log" }
$listen = netstat -ano | Select-String ':443\s+.*LISTENING'
Step ("proxy PID " + $p.Id + " started; 443 listening: " + $(if ($listen) { 'YES' } else { 'NO' }))
Step "env: HD2_GWE_DUMP=$Dump PATHS=$Paths REQ_PATHS=$ReqPaths"
Step "in game: galaxy map -> CHARBAL-VII(156) -> DEFENSE card -> SELECT CAMPAIGN"
