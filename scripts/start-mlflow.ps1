# Starts the local MLflow tracking server (SQLite backend + local artifact store).
# Usage (from anywhere): powershell -ExecutionPolicy Bypass -File scripts/start-mlflow.ps1

$ErrorActionPreference = "Stop"

# Project root = parent folder of this script, wherever the repo was cloned
$projectRoot = Join-Path $PSScriptRoot ".."

Push-Location $projectRoot
try {
    uv run mlflow server `
        --backend-store-uri sqlite:///mlflow.db `
        --artifacts-destination ./mlartifacts `
        --host 127.0.0.1 `
        --port 5000
}
finally {
    # Always return to the caller's folder, even after Ctrl+C or an error
    Pop-Location
}
