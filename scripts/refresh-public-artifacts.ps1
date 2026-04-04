param(
  [string]$RunId = "refresh-public"
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$repoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$sampleRidesPath = Join-Path $repoRoot "data/samples/raw/PFDA_rides.csv"
$sampleWeatherPath = Join-Path $repoRoot "data/samples/raw/PFDA_weather.csv"
$pythonCandidates = @(
  (Join-Path $repoRoot ".venv/Scripts/python.exe"),
  (Join-Path $repoRoot ".venv/bin/python")
)

$pythonExecutable = $null
foreach ($candidate in $pythonCandidates) {
  if (Test-Path $candidate) {
    $pythonExecutable = $candidate
    break
  }
}

if (-not $pythonExecutable) {
  $pythonExecutable = "python"
}

function Invoke-RideFareStep {
  param(
    [string]$Label,
    [string[]]$Arguments
  )

  Write-Host "==> $Label"
  & $pythonExecutable @Arguments
  if ($LASTEXITCODE -ne 0) {
    throw "RideFare step failed: $Label"
  }
}

Push-Location $repoRoot
try {
  Invoke-RideFareStep -Label "Ingest sample data" -Arguments @(
    "-m",
    "ridefare",
    "ingest",
    "--rides-path",
    $sampleRidesPath,
    "--weather-path",
    $sampleWeatherPath
  )

  Invoke-RideFareStep -Label "Transform marts" -Arguments @(
    "-m",
    "ridefare",
    "transform"
  )

  Invoke-RideFareStep -Label "Train ML workflow" -Arguments @(
    "-m",
    "ridefare",
    "train",
    "--run-id",
    $RunId
  )

  Invoke-RideFareStep -Label "Export public web artifacts" -Arguments @(
    "-m",
    "ridefare",
    "export-web",
    "--run-id",
    $RunId
  )

  Write-Host "Public web artifacts refreshed successfully."
  Write-Host "ML web artifacts: $(Join-Path $repoRoot 'data/processed/ml/web')"
  Write-Host "Analytics web artifacts: $(Join-Path $repoRoot 'data/processed/analytics/web')"
} finally {
  Pop-Location
}
