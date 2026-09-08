# Start both backends for local development.
#   - Node runner service on :8787 (in a new window)
#   - FastAPI app on :8010 (this window)
#
# One-time setup:
#   npm install                              # in this folder (links the shared client + express)
#   python -m venv .venv ; .\.venv\Scripts\pip install -r backend-python\requirements-dev.txt

$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $PSScriptRoot
Set-Location $root

if (-not (Test-Path "$root\node_modules\elo-playground")) {
    Write-Host "node_modules missing - running 'npm install' ..." -ForegroundColor Yellow
    npm install
}

# Node runner in its own window so its logs stay separate.
Start-Process -FilePath "node" -ArgumentList "backend-node/src/server.mjs" -WorkingDirectory $root

Start-Sleep -Seconds 1

$py = if (Test-Path "$root\.venv\Scripts\python.exe") { "$root\.venv\Scripts\python.exe" }
      elseif (Test-Path "$root\..\.venv\Scripts\python.exe") { "$root\..\.venv\Scripts\python.exe" }
      else { "python" }
Set-Location "$root\backend-python"
& $py -m uvicorn app.main:app --host 127.0.0.1 --port 8010
