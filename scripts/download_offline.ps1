# Download Python wheels and the npm cache for an offline install.
# Run this once on a machine that has internet, Python, and Node.js.
# Wheels match this Windows machine and this Python version.

$ErrorActionPreference = "Stop"
$Root = Resolve-Path (Join-Path $PSScriptRoot "..")
$WheelDir = Join-Path $Root "offline\wheels"
$NpmCache = Join-Path $Root "offline\npm-cache"
$VenvPython = Join-Path $Root "backend\.venv\Scripts\python.exe"
$Requirements = Join-Path $Root "backend\requirements.txt"

New-Item -ItemType Directory -Force -Path $WheelDir, $NpmCache | Out-Null

if (-not (Test-Path $VenvPython)) {
    Write-Host "Creating backend virtual environment..."
    python -m venv (Join-Path $Root "backend\.venv")
}

Write-Host "Downloading Python wheels into $WheelDir"
& $VenvPython -m pip install --upgrade pip
if ($LASTEXITCODE -ne 0) { throw "pip upgrade failed with exit code $LASTEXITCODE" }
& $VenvPython -m pip download --only-binary=:all: -r $Requirements -d $WheelDir
if ($LASTEXITCODE -ne 0) { throw "pip download failed with exit code $LASTEXITCODE" }

# Install in a side folder so a running dev server can keep its node_modules.
$Stage = Join-Path $Root "offline\npm-stage"
if (Test-Path $Stage) { Remove-Item $Stage -Recurse -Force }
New-Item -ItemType Directory -Force -Path $Stage | Out-Null
Copy-Item (Join-Path $Root "frontend\package.json") $Stage
Copy-Item (Join-Path $Root "frontend\package-lock.json") $Stage

Write-Host "Filling the npm cache at $NpmCache"
Push-Location $Stage
npm ci --cache $NpmCache
$npmCode = $LASTEXITCODE
Pop-Location
if ($npmCode -ne 0) { throw "npm ci failed with exit code $npmCode" }
Remove-Item $Stage -Recurse -Force

$WheelCount = (Get-ChildItem $WheelDir -File).Count
Write-Host ""
Write-Host "Saved $WheelCount wheels and the npm cache under $Root\offline"
Write-Host "Copy the whole MQIH folder to the offline machine, then run scripts\install_offline.ps1"
