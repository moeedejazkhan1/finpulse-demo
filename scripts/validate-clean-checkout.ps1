# T034 - full clean-checkout validation (spec.md SC-001 through SC-004).
# Run this once Docker Desktop is installed and running. Safe to re-run.
#
# Usage: powershell -ExecutionPolicy Bypass -File scripts\validate-clean-checkout.ps1

$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $PSScriptRoot

Write-Host "==> Tearing down any existing stack (clean checkout simulation)"
docker compose -f "$root\docker-compose.yml" down -v

Write-Host "==> Building images"
docker compose -f "$root\docker-compose.yml" build

Write-Host "==> Starting the stack"
docker compose -f "$root\docker-compose.yml" up -d

Write-Host "==> Waiting for airflow-webserver to report healthy (this can take a few minutes on first boot)"
$deadline = (Get-Date).AddMinutes(10)
do {
    Start-Sleep -Seconds 10
    $status = docker inspect --format='{{.State.Health.Status}}' finpulse-demo-airflow-webserver-1 2>$null
    Write-Host "  airflow-webserver: $status"
} while ($status -ne "healthy" -and (Get-Date) -lt $deadline)

if ($status -ne "healthy") {
    Write-Warning "airflow-webserver did not report healthy within the timeout -- check 'docker compose logs airflow-webserver'"
}

Write-Host "==> Triggering batch_load_dag and fraud_scoring_dag"
docker compose -f "$root\docker-compose.yml" exec -T airflow-webserver airflow dags trigger batch_load_dag
Start-Sleep -Seconds 5
docker compose -f "$root\docker-compose.yml" exec -T airflow-webserver airflow dags trigger fraud_scoring_dag

Write-Host ""
Write-Host "==> Stack is up. Next steps:"
Write-Host "    - Airflow UI:   http://localhost:8080  (admin / admin)"
Write-Host "    - Metabase:     http://localhost:3000  (admin@finpulse.local / FinPulseDemo123!)"
Write-Host "    - MinIO console: http://localhost:9001 (finpulse / finpulse123)"
Write-Host ""
Write-Host "==> Once both DAGs show 'success' in the Airflow UI, run the integration tests:"
Write-Host "    pytest tests/integration/test_end_to_end.py -v"
