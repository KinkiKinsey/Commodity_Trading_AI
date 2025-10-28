Param(
    [string]$Uri = "https://www.bloomberg.com/quote/WTI:US",
    [string]$OutputPath = "$(Split-Path -Parent $MyInvocation.MyCommand.Path)\raw\wti_quote.html",
    [string]$LogPath = "$(Split-Path -Parent $MyInvocation.MyCommand.Path)\fetch_log.md"
)

# Ensure output directory exists
$outDir = Split-Path -Parent $OutputPath
if (-not (Test-Path $outDir)) {
    New-Item -ItemType Directory -Path $outDir | Out-Null
}

$timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ssK"

Write-Host "Fetching $Uri ..."
try {
    $response = Invoke-WebRequest -Uri $Uri -Headers @{
        "User-Agent"      = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
        "Accept-Language" = "en-US,en;q=0.9"
    } -TimeoutSec 30

    $response.Content | Out-File -FilePath $OutputPath -Encoding UTF8

    $logEntry = @"
### $timestamp
- URI: $Uri
- Status code: $($response.StatusCode)
- Output: $OutputPath

"@
    $logEntry | Out-File -FilePath $LogPath -Encoding UTF8 -Append

    Write-Host "Snapshot saved to $OutputPath"
} catch {
    $logEntry = @"
### $timestamp
- URI: $Uri
- Error: $($_.Exception.Message)

"@
    $logEntry | Out-File -FilePath $LogPath -Encoding UTF8 -Append
    throw
}
