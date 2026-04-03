try {
  py -3.13 --version | Out-Null
} catch {
  Write-Error "Python 3.13 is required for RideFare. Install it before running bootstrap."
  exit 1
}

py -3.13 -m venv .venv
.\.venv\Scripts\python -m pip install --upgrade pip
.\.venv\Scripts\python -m pip install -e .[data,ml,dev]
corepack pnpm install
