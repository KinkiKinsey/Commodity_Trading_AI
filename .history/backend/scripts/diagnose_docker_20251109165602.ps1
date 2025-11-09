# 检查 Docker compose 服务状态、端口映射，以及 ClickHouse 是否可读
$composeFile = "..\docker-compose.ctp.yml"
if (-not (Test-Path $composeFile)) {
    Write-Host "❌ 找不到 docker-compose.ctp.yml ($composeFile)" -ForegroundColor Red
    exit 1
}

Write-Host "=== Docker compose ps ===" -ForegroundColor Cyan
docker compose -f $composeFile ps

Write-Host "`n=== 端口连通性 (ClickHouse/Kafka) ===" -ForegroundColor Cyan
$services = @(
    @{ Name = "ClickHouse HTTP"; Host = "127.0.0.1"; Port = 18123 },
    @{ Name = "Kafka"; Host = "127.0.0.1"; Port = 9094 }
)

foreach ($svc in $services) {
    $result = Test-NetConnection -ComputerName $svc.Host -Port $svc.Port
    if ($result.TcpTestSucceeded) {
        Write-Host "✅ $($svc.Name) 可连接 ($($svc.Host):$($svc.Port))"
    } else {
        Write-Host "❌ $($svc.Name) 无法连接 ($($svc.Host):$($svc.Port))" -ForegroundColor Red
    }
}

Write-Host "`n=== ClickHouse 数据示例 ===" -ForegroundColor Cyan
try {
    $resp = curl.exe "http://127.0.0.1:18123/?query=SELECT%20symbol,local_ts,last_price%20FROM%20ctp.ctp_ticks%20ORDER%20BY%20local_ts%20DESC%20LIMIT%205%20FORMAT%20JSON"
    Write-Output $resp
} catch {
    Write-Host "❌ 无法访问 ClickHouse HTTP API: $_" -ForegroundColor Red
}
