# Run after Metabase (start-metabase.ps1) has finished its first boot.
$root = Split-Path -Parent (Split-Path -Parent $PSScriptRoot)

$env:METABASE_URL = "http://localhost:3000"
$env:POSTGRES_HOST = "localhost"
$env:POSTGRES_PORT = "5432"
$env:POSTGRES_DB = "finpulse"
$env:POSTGRES_USER = "finpulse"
$env:POSTGRES_PASSWORD = "finpulse"

& "$root\.venv311\Scripts\python.exe" "$root\infra\metabase\provision_dashboard.py"
