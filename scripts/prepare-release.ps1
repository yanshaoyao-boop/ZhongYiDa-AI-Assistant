param(
    [switch]$SkipFrontendBuild
)

$ErrorActionPreference = "Stop"

$repoRoot = Split-Path -Parent $PSScriptRoot
$releaseRoot = Join-Path $repoRoot "release-artifacts"
$stageRoot = Join-Path $releaseRoot "stage"
$backendStage = Join-Path $stageRoot "backend"
$frontendStage = Join-Path $stageRoot "frontend"

function Reset-Directory([string]$Path) {
    if (Test-Path $Path) {
        Remove-Item $Path -Recurse -Force
    }
    New-Item -ItemType Directory -Path $Path | Out-Null
}

Reset-Directory $stageRoot
New-Item -ItemType Directory -Path $backendStage | Out-Null
New-Item -ItemType Directory -Path $frontendStage | Out-Null

$frontendRoot = Join-Path $repoRoot "frontend"
$backendRoot = Join-Path $repoRoot "backend"

if (-not $SkipFrontendBuild) {
    Push-Location $frontendRoot
    try {
        npm run build
    }
    finally {
        Pop-Location
    }
}

$backendFiles = @(
    "main.py",
    "database.py",
    "dependencies.py",
    "requirements.txt",
    ".env.example"
)

$backendDirs = @(
    "models",
    "routers",
    "services",
    "scripts",
    "deploy"
)

foreach ($file in $backendFiles) {
    $source = Join-Path $backendRoot $file
    if (Test-Path $source) {
        Copy-Item $source -Destination (Join-Path $backendStage $file) -Force
    }
}

foreach ($dir in $backendDirs) {
    $source = Join-Path $backendRoot $dir
    if (Test-Path $source) {
        Copy-Item $source -Destination (Join-Path $backendStage $dir) -Recurse -Force
    }
}

$frontendDist = Join-Path $frontendRoot "dist"
if (-not (Test-Path $frontendDist)) {
    throw "frontend/dist does not exist. Build the frontend first."
}

Copy-Item $frontendDist -Destination (Join-Path $frontendStage "dist") -Recurse -Force

$backendZip = Join-Path $releaseRoot "backend-release.zip"
$frontendZip = Join-Path $releaseRoot "frontend-release.zip"

if (Test-Path $backendZip) { Remove-Item $backendZip -Force }
if (Test-Path $frontendZip) { Remove-Item $frontendZip -Force }

Compress-Archive -Path (Join-Path $backendStage "*") -DestinationPath $backendZip -Force
Compress-Archive -Path (Join-Path $frontendStage "*") -DestinationPath $frontendZip -Force

Write-Host "Safe release packages created:"
Write-Host " - $backendZip"
Write-Host " - $frontendZip"
Write-Host ""
Write-Host "Excluded from packages:"
Write-Host " - backend/.env"
Write-Host " - backend/data"
Write-Host " - backend/venv"
Write-Host " - any private local-only folders"
