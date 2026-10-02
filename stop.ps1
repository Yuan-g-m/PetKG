$ErrorActionPreference = 'SilentlyContinue'
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8

$ProjectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$JdkHome = Join-Path $ProjectRoot 'runtime\jdk-11.0.32.1+1'

foreach ($port in 8000, 8501) {
    $connections = Get-NetTCPConnection -LocalPort $port -State Listen
    foreach ($connection in $connections) {
        Stop-Process -Id $connection.OwningProcess -Force
    }
}

Get-Process java | Where-Object { $_.Path -like "$JdkHome*" } | Stop-Process -Force
Get-CimInstance Win32_Process -Filter "Name='cmd.exe'" | Where-Object { $_.CommandLine -like '*PetKG*runtime*neo4j*console*' } | ForEach-Object {
    Stop-Process -Id $_.ProcessId -Force
}

Write-Host 'PetKG stopped.'
