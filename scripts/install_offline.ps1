# Install the backend and frontend from the local offline folder.
# No network access is required. Python and Node.js must already be installed.
# Run scripts\download_offline.ps1 on a connected machine of the same OS and Python version first.

$ErrorActionPreference = "Stop"
$Root = Resolve-Path (Join-Path $PSScriptRoot "..")
$WheelDir = Join-Path $Root "offline\wheels"
$NpmCache = Join-Path $Root "offline\npm-cache"
$VenvDir = Join-Path $Root "backend\.venv"
$VenvPython = Join-Path $VenvDir "Scripts\python.exe"
$Requirements = Join-Path $Root "backend\requirements.txt"

if (-not (Test-Path $WheelDir)) {
    throw "Missing $WheelDir. Run scripts\download_offline.ps1 on a machine with internet first."
}
if (-not (Test-Path $NpmCache)) {
    throw "Missing $NpmCache. Run scripts\download_offline.ps1 on a machine with internet first."
}

if (-not (Test-Path $VenvPython)) {
    Write-Host "Creating backend virtual environment..."
    python -m venv $VenvDir
}

Write-Host "Installing Python packages from $WheelDir"
& $VenvPython -m pip install --no-index --find-links $WheelDir -r $Requirements

Write-Host "Installing frontend packages from the local npm cache"
Push-Location (Join-Path $Root "frontend")
npm ci --offline --cache $NpmCache
Pop-Location

Write-Host ""
Write-Host "Offline install finished."
Write-Host "API:  $VenvPython -m uvicorn app.main:app --host 127.0.0.1 --port 8000"
Write-Host "UI:   npm run dev    (from the frontend folder)"
