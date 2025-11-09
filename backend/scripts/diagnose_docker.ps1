param(
    [string]$ComposePath = "../docker-compose.ctp.yml",
    [string]$ClickhousePort = "18123",
    [string]$KafkaPort = "9094"
)

function Test-Port {
    param(
        [string]$TargetHost,
        [int]$TargetPort,
        [string]$Name
    )
    $connectionResult = Test-NetConnection -ComputerName $TargetHost -Port $TargetPort -WarningAction SilentlyContinue
    if ($connectionResult.TcpTestSucceeded) {
        Write-Host ("Success: {0} ({1}:{2})" -f $Name, $TargetHost, $TargetPort)
    } else {
        Write-Host ("Failed: {0} ({1}:{2})" -f $Name, $TargetHost, $TargetPort) -ForegroundColor Red
    }
}

$composeFullPath = Resolve-Path -LiteralPath $ComposePath -ErrorAction SilentlyContinue
if (-not $composeFullPath) {
    $composeFullPath = Resolve-Path -LiteralPath "./docker-compose.ctp.yml" -ErrorAction SilentlyContinue
}
if (-not $composeFullPath) {
    Write-Host "Cannot find docker-compose.ctp.yml (tried $ComposePath and ./docker-compose.ctp.yml)" -ForegroundColor Red
    exit 1
}

Write-Host "=== Docker compose ps ==="
docker compose -f $composeFullPath ps

Write-Host "`n=== Port connectivity (ClickHouse/Kafka) ==="
Test-Port -TargetHost "127.0.0.1" -TargetPort ([int]$ClickhousePort) -Name "ClickHouse HTTP"
Test-Port -TargetHost "127.0.0.1" -TargetPort ([int]$KafkaPort) -Name "Kafka"

Write-Host "`n=== ClickHouse sample data ==="
try {
    $query = "SELECT symbol, local_ts, last_price FROM ctp.ctp_ticks ORDER BY local_ts DESC LIMIT 5 FORMAT JSON"
    $encoded = [uri]::EscapeDataString($query)
    $resp = curl.exe "http://127.0.0.1:$ClickhousePort/?query=$encoded"
    Write-Output $resp
} catch {
    Write-Host "Cannot access ClickHouse HTTP API: $_" -ForegroundColor Red
}
