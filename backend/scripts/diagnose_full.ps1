param(
    [string]$ComposePath = "../docker-compose.ctp.yml",
    [string]$ClickhouseUrl = "http://127.0.0.1:18123",
    [string]$BackendUrl = "http://localhost:8000"
)

$ErrorActionPreference = "Stop"
$log = @()
function Write-Log {
    param([string]$Message)
    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    $log += "[$timestamp] $Message"
}

try {
    $composeFullPath = Resolve-Path -LiteralPath $ComposePath -ErrorAction Stop
    Write-Log "docker-compose file located at $composeFullPath"
} catch {
    Write-Log "Cannot find docker-compose file: $_"
    $log | Set-Content backend/scripts/diagnose_full.log
    exit 1
}

Write-Log "=== docker compose ps ==="
$log += docker compose -f $composeFullPath ps

Write-Log "=== docker logs (last 20 lines) ==="
foreach ($svc in @("clickhouse", "kafka", "collector")) {
    $log += "--- $svc logs ---"
    $log += docker compose -f $composeFullPath logs --tail 20 $svc
}

Write-Log "=== ClickHouse sample data ==="
try {
    $query = [uri]::EscapeDataString("SELECT symbol, local_ts, last_price FROM ctp.ctp_ticks ORDER BY local_ts DESC LIMIT 5 FORMAT JSON")
    $resp = curl.exe "$ClickhouseUrl/?query=$query"
    $log += $resp
} catch {
    Write-Log "ClickHouse request failed: $_"
}

Write-Log "=== Backend endpoints ==="
$endpoints = @(
    "$BackendUrl/api/ctp/realtime?symbol=CL2512-NYM",
    "$BackendUrl/api/ctp/kline?symbol=CL2512-NYM&interval=5m&count=120",
    "$BackendUrl/api/pricing/tick?instrument_id=CL2512-NYM"
)
foreach ($endpoint in $endpoints) {
    try {
        $log += "--- $endpoint ---"
        $log += curl.exe $endpoint
    } catch {
        Write-Log ("Failed to call {0}: {1}" -f $endpoint, $_)
    }
}

$log | Set-Content backend/scripts/diagnose_full.log
Write-Host "Diagnose log written to backend/scripts/diagnose_full.log"
