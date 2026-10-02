$ErrorActionPreference = 'Stop'
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8

$ProjectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location -LiteralPath $ProjectRoot

$PythonPathFile = Join-Path $ProjectRoot 'runtime\python-path.txt'
$ConfiguredPython = $null
if ($env:PETKG_PYTHON -and (Test-Path -LiteralPath $env:PETKG_PYTHON)) {
    $ConfiguredPython = $env:PETKG_PYTHON
}
elseif (Test-Path -LiteralPath $PythonPathFile) {
    $ConfiguredPython = (Get-Content -LiteralPath $PythonPathFile -TotalCount 1 | Select-Object -First 1).Trim()
}

$PythonCandidates = @(
    $ConfiguredPython,
    (Join-Path $ProjectRoot 'runtime\python\python.exe')
)
$Python = $null
foreach ($Candidate in $PythonCandidates) {
    if ($Candidate -and (Test-Path -LiteralPath $Candidate)) {
        $Python = $Candidate
        break
    }
}
if (-not $Python) {
    $PythonCommand = Get-Command python -ErrorAction SilentlyContinue
    if ($PythonCommand) {
        $Python = $PythonCommand.Source
    }
}
if (-not $Python) {
    throw 'Python not found. Set PETKG_PYTHON to your Python executable or install Python first.'
}

$PythonRoot = Split-Path -Parent $Python
$Uvicorn = Join-Path $PythonRoot 'Scripts\uvicorn.exe'
$Streamlit = Join-Path $PythonRoot 'Scripts\streamlit.exe'
$CertFile = Join-Path $PythonRoot 'lib\site-packages\certifi\cacert.pem'

$JdkHome = Join-Path $ProjectRoot 'runtime\jdk-11.0.32.1+1'
$Neo4jHome = Join-Path $ProjectRoot 'runtime\neo4j-community-4.4.41'
$Neo4jBat = Join-Path $Neo4jHome 'bin\neo4j.bat'
$LogDir = Join-Path $ProjectRoot 'runtime\logs'

if (-not (Test-Path -LiteralPath $JdkHome)) {
    throw 'runtime\jdk-11.0.32.1+1 not found. Follow README to place the portable JDK runtime first.'
}
if (-not (Test-Path -LiteralPath $Neo4jHome)) {
    throw 'runtime\neo4j-community-4.4.41 not found. Follow README to place the local Neo4j runtime first.'
}

New-Item -ItemType Directory -Force -Path $LogDir | Out-Null

$env:PYTHONPATH = $ProjectRoot
$env:PYTHONIOENCODING = 'utf-8'
$env:SSL_CERT_FILE = $CertFile
$env:NO_PROXY = '127.0.0.1,localhost'
$env:no_proxy = '127.0.0.1,localhost'
$env:JAVA_HOME = $JdkHome
$env:NEO4J_HOME = $Neo4jHome

function Test-Port {
    param([int]$Port)
    $client = New-Object System.Net.Sockets.TcpClient
    try {
        $result = $client.BeginConnect('127.0.0.1', $Port, $null, $null)
        if ($result.AsyncWaitHandle.WaitOne(500)) {
            $client.EndConnect($result)
            return $true
        }
        return $false
    }
    catch {
        return $false
    }
    finally {
        $client.Close()
    }
}

function Wait-Port {
    param([int]$Port, [int]$TimeoutSec = 120)
    $deadline = (Get-Date).AddSeconds($TimeoutSec)
    while ((Get-Date) -lt $deadline) {
        if (Test-Port -Port $Port) {
            return $true
        }
        Start-Sleep -Milliseconds 500
    }
    return (Test-Port -Port $Port)
}

try {
    if (-not (Test-Port -Port 7687)) {
        Write-Host '[1/3] Starting Neo4j...'
        Start-Process -FilePath $Neo4jBat -ArgumentList 'console' -WorkingDirectory $Neo4jHome -WindowStyle Hidden -RedirectStandardOutput (Join-Path $LogDir 'neo4j-console.out.log') -RedirectStandardError (Join-Path $LogDir 'neo4j-console.err.log')
        if (-not (Wait-Port -Port 7687 -TimeoutSec 90)) {
            throw 'Neo4j failed to start. See runtime\logs\neo4j-console.err.log'
        }
        Write-Host 'Neo4j started.'
    }
    else {
        Write-Host '[1/3] Neo4j is already running.'
    }

    if (-not (Test-Port -Port 8000)) {
        Write-Host '[2/3] Starting FastAPI...'
        Start-Process -FilePath $Uvicorn -ArgumentList @('__005__fastapi.my_fastapi:app', '--host', '0.0.0.0', '--port', '8000') -WorkingDirectory $ProjectRoot -WindowStyle Hidden -RedirectStandardOutput (Join-Path $LogDir 'fastapi.out.log') -RedirectStandardError (Join-Path $LogDir 'fastapi.err.log')
        if (-not (Wait-Port -Port 8000 -TimeoutSec 180)) {
            throw 'FastAPI failed to start. See runtime\logs\fastapi.err.log'
        }
        Write-Host 'FastAPI started.'
    }
    else {
        Write-Host '[2/3] FastAPI is already running.'
    }

    if (-not (Test-Port -Port 8501)) {
        Write-Host '[3/3] Starting Streamlit...'
        Start-Process -FilePath $Streamlit -ArgumentList @('run', '__006__streamlit/__001__streamlit_chat_page.py', '--server.address', '127.0.0.1', '--server.port', '8501', '--server.headless', 'true') -WorkingDirectory $ProjectRoot -WindowStyle Hidden -RedirectStandardOutput (Join-Path $LogDir 'streamlit.out.log') -RedirectStandardError (Join-Path $LogDir 'streamlit.err.log')
        if (-not (Wait-Port -Port 8501 -TimeoutSec 180)) {
            throw 'Streamlit failed to start. See runtime\logs\streamlit.err.log'
        }
        Write-Host 'Streamlit started.'
    }
    else {
        Write-Host '[3/3] Streamlit is already running.'
    }

    Write-Host ''
    Write-Host 'PetKG is ready:'
    Write-Host '  Neo4j:    bolt://127.0.0.1:7687'
    Write-Host '  FastAPI:  http://127.0.0.1:8000'
    Write-Host '  Streamlit: http://127.0.0.1:8501'
    Start-Process 'http://127.0.0.1:8501'
}
catch {
    Write-Host ''
    Write-Host ('Startup failed: ' + $_.Exception.Message) -ForegroundColor Red
    Write-Host 'Log directory: ' + $LogDir
    Read-Host 'Press Enter to exit'
    exit 1
}
