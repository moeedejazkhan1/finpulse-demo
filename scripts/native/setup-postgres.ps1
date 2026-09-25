# One-time setup: extracts the portable Postgres binaries, initializes
# a data directory, and starts the server on port 5432.
# Re-running is safe -- it skips steps that already happened.

$ErrorActionPreference = "Stop"
$root = Split-Path -Parent (Split-Path -Parent $PSScriptRoot)
$runtime = "$root\runtime"
$pgHome = "$runtime\pgsql"
$dataDir = "$runtime\pgdata"

if (-not (Test-Path $pgHome)) {
    Write-Host "==> Extracting Postgres binaries"
    Expand-Archive -Path "$runtime\postgres.zip" -DestinationPath $runtime -Force
}

$env:PATH = "$pgHome\bin;$env:PATH"

if (-not (Test-Path $dataDir)) {
    Write-Host "==> Initializing data directory"
    $pwFile = New-TemporaryFile
    Set-Content -Path $pwFile -Value "finpulse" -NoNewline
    & "$pgHome\bin\initdb.exe" -D $dataDir -U finpulse --pwfile="$pwFile" --auth=trust
    Remove-Item $pwFile
}

Write-Host "==> Starting Postgres on port 5432 (logs: $runtime\pg.log)"
& "$pgHome\bin\pg_ctl.exe" -D $dataDir -l "$runtime\pg.log" -o "-p 5432" start

Start-Sleep -Seconds 3

Write-Host "==> Creating finpulse database + schemas"
$env:PGPASSWORD = "finpulse"
& "$pgHome\bin\psql.exe" -U finpulse -h localhost -p 5432 -d postgres -c "CREATE DATABASE finpulse;" 2>$null
& "$pgHome\bin\psql.exe" -U finpulse -h localhost -p 5432 -d finpulse -f "$root\infra\postgres\init_native.sql"

Write-Host "==> Postgres ready at localhost:5432 (user=finpulse password=finpulse db=finpulse)"
