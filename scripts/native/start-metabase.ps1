# Starts Metabase natively via the portable JDK, using its own local
# H2 app-database (default) so no extra Postgres database is needed for
# Metabase's internal state. Metabase then gets pointed at our
# `finpulse` warehouse database separately by provision_dashboard.py.

$root = Split-Path -Parent (Split-Path -Parent $PSScriptRoot)
$runtime = "$root\runtime"
$jdkBin = Get-ChildItem "$runtime\jdk" -Directory | Select-Object -First 1
$java = "$($jdkBin.FullName)\bin\java.exe"

Write-Host "==> Starting Metabase on http://localhost:3000 (first boot takes 1-2 minutes)"
& $java -jar "$runtime\metabase.jar"
