$ErrorActionPreference = "Stop"
Set-Location (Join-Path $PSScriptRoot "..")
if (-Not (Test-Path ".venv")) {
    Write-Error "Missing .venv. Run .\scripts\setup-prj.ps1 first."
}
.\.venv\Scripts\pocketflow-creator.exe @args
