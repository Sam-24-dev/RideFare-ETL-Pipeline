$pythonExe = ".\.venv\Scripts\python.exe"

if (-not (Test-Path $pythonExe)) {
  Write-Error "Missing .venv\\Scripts\\python. Run scripts\\bootstrap.ps1 first."
  exit 1
}

$pythonVersion = & $pythonExe -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')"
if ($pythonVersion -ne "3.13") {
  Write-Error "RideFare validation expects Python 3.13 inside .venv. Current version: $pythonVersion"
  exit 1
}

& $pythonExe -m ruff check .
& $pythonExe -m pytest
