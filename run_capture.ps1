# run_capture.ps1 -- recon run: capture API responses, rewrite nothing.
#
# ASCII-ONLY ON PURPOSE: Windows PowerShell 5.1 parses BOM-less UTF-8 as ANSI, so any
# non-ASCII character in this file breaks the parser. Keep it English/ASCII.
#
# WHY: the capture run needs the server's ORIGINAL bodies (effect menu + war status), so it
# starts the proxy with -Passthrough: zero rewriting, zero injection.
#
# USAGE (normal user; only the install step below needs admin):
#   powershell -ExecutionPolicy Bypass -File run_capture.ps1
#   powershell -ExecutionPolicy Bypass -File run_capture.ps1 -Paths "/api/WarSeason/GalacticWarEffects"
#   powershell -ExecutionPolicy Bypass -File run_capture.ps1 -Rewrite    # later: inject + capture
#
# PREREQ (one-time, admin):
#   cd D:\Downloads\variant_mod
#   powershell -ExecutionPolicy Bypass -File setup.ps1
# If the game cannot reach the server after install, set config.json listenIp to a real
# local adapter IP (not 127.x) and re-run setup.ps1.

param(
    [string]$DumpDir = "D:\mod\out\gwe",
    [string]$Paths = "/api/WarSeason/GalacticWarEffects,/Status",
    [int]$MaxBytes = 8388608,
    [switch]$Rewrite
)

$ErrorActionPreference = 'Stop'
$root = "D:\Downloads\variant_mod"

Write-Host "[capture] dump dir : $DumpDir"
Write-Host "[capture] whitelist: $Paths"
if ($Rewrite) {
    Write-Host "[capture] mode     : REWRITE (injects variants, then captures)"
} else {
    Write-Host "[capture] mode     : Passthrough (recon only, nothing rewritten)"
}

# --- proxy / clash preflight ------------------------------------------------
# Three independent interference surfaces:
#   1) WinINET system proxy   -> components using WinINET/WinHTTP get pulled into Clash
#   2) HTTP(S)_PROXY env vars -> libcurl honours them, requests go to Clash, hosts is ignored
#   3) TUN mode               -> takes over routing, panel may pick the fake TUN IP
Write-Host "[capture] --- preflight ---"
$wininet = Get-ItemProperty 'HKCU:\Software\Microsoft\Windows\CurrentVersion\Internet Settings' -ErrorAction SilentlyContinue
if ($wininet -and $wininet.ProxyEnable -eq 1) {
    Write-Host "[capture] WinINET proxy  : $($wininet.ProxyServer)   <-- consider turning it off"
} else {
    Write-Host "[capture] WinINET proxy  : off"
}
$envNames = @('HTTP_PROXY', 'HTTPS_PROXY', 'ALL_PROXY', 'http_proxy', 'https_proxy')
$hit = @()
foreach ($n in $envNames) {
    $v = (Get-Item "Env:$n" -ErrorAction SilentlyContinue).Value
    if ($v) { $hit += $n }
}
if ($hit.Count -gt 0) {
    Write-Host "[capture] proxy env     : $($hit -join ',')   <-- game bypasses hosts if it inherits these"
} else {
    Write-Host "[capture] proxy env     : none"
}
$tun = Get-NetIPAddress -AddressFamily IPv4 -ErrorAction SilentlyContinue |
       Where-Object { $_.IPAddress -like '198.18.*' -or $_.InterfaceAlias -match 'Tun|Clash|Mihomo' }
if ($tun) {
    Write-Host "[capture] TUN mode      : $($tun.InterfaceAlias -join ',')   <-- turn it off before testing"
} else {
    Write-Host "[capture] TUN mode      : off"
}
# Direct-route check for the UPSTREAM hop.
# After install the hosts line points the API name at the local listener, so a plain request
# would hit us instead of the real server. Resolve the real address through an explicit public
# resolver (that ignores hosts) and connect by IP via --resolve.
$apiHost = 'api.live.prod.thehelldiversgame.com'
$realIp = ''
foreach ($srv in @('223.5.5.5', '1.1.1.1', '8.8.8.8')) {
    try {
        $ans = Resolve-DnsName -Name $apiHost -Type A -Server $srv -ErrorAction Stop |
               Where-Object { $_.IPAddress } | Select-Object -First 1
        if ($ans) { $realIp = $ans.IPAddress; break }
    } catch { }
}
if ($realIp) {
    $probe = & curl.exe -s -o NUL -w "%{http_code}" --noproxy '*' --max-time 15 `
             --resolve "${apiHost}:443:$realIp" -H "Connection: close" `
             "https://${apiHost}/api/WarSeason/current/WarId" 2>$null
    if ($probe -eq '200') {
        Write-Host "[capture] upstream hop   : HTTP 200 via $realIp  OK (Clash not needed for this hop)"
    } else {
        Write-Host "[capture] upstream hop   : HTTP $probe via $realIp   <-- direct route broken, fix before testing"
    }
} else {
    Write-Host "[capture] upstream hop   : could not resolve the real IP (public resolvers unreachable)"
}
Write-Host "[capture] advice: quit Clash Verge for this run (or at least disable system proxy + TUN)."

# --- install preconditions --------------------------------------------------
if (-not (Test-Path (Join-Path $root 'certs\session.json'))) {
    Write-Host "[capture] ERROR: no session certificate. Run as admin first:"
    Write-Host "          cd $root"
    Write-Host "          powershell -ExecutionPolicy Bypass -File setup.ps1"
    exit 1
}
$hostsFile = Join-Path $env:SystemRoot 'System32\drivers\etc\hosts'
$marker = Select-String -Path $hostsFile -Pattern '# variant-mod' -ErrorAction SilentlyContinue
if (-not $marker) {
    Write-Host "[capture] ERROR: no '# variant-mod' line in hosts. Run setup.ps1 (admin)."
    exit 1
}
$pidFile = Join-Path $root 'logs\pids.json'
if (Test-Path $pidFile) {
    $rec = $null
    try { $rec = Get-Content $pidFile -Raw | ConvertFrom-Json } catch { }
    $alive = $false
    if ($rec -and $rec.proxy) {
        $alive = [bool](Get-Process -Id $rec.proxy -ErrorAction SilentlyContinue)
    }
    if ($alive) {
        Write-Host "[capture] already running (pid $($rec.proxy), started $($rec.started)) -- reuse it."
        Write-Host "[capture] just launch the game: log in, reach the ship, switch planet once."
        Write-Host "[capture] when done: $root\stop.ps1"
        Write-Host "[capture] captured bodies: $DumpDir\index.txt"
        exit 0
    }
    Write-Host "[capture] stale session record (pid $($rec.proxy) is gone) -- cleaning up and continuing."
    Remove-Item $pidFile -Force -ErrorAction SilentlyContinue
}

# --- switches (Start-Process inherits the parent environment) ----------------
New-Item -ItemType Directory -Force -Path $DumpDir | Out-Null
$env:HD2_GWE_DUMP = $DumpDir
$env:HD2_GWE_PATHS = $Paths
$env:HD2_GWE_MAX = "$MaxBytes"

# --- start ------------------------------------------------------------------
if ($Rewrite) {
    & (Join-Path $root 'run.ps1')
} else {
    & (Join-Path $root 'run.ps1') -Passthrough
}

Write-Host ""
Write-Host "[capture] in game:"
Write-Host "          1) log in and reach the ship (GalacticWarEffects is fetched at login)"
Write-Host "          2) open the galaxy map and switch planet once (forces a Status refresh)"
Write-Host "          3) play a bit, then stop with: $root\stop.ps1"
Write-Host "[capture] captured bodies: $DumpDir\index.txt"
