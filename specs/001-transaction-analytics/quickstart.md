# Quickstart: FinPulse Transaction Analytics Platform

Validates the platform end-to-end against spec.md's success criteria. See
[data-model.md](./data-model.md) and [contracts/transaction-event-schema.md](./contracts/transaction-event-schema.md)
for schema details — not repeated here.

## Prerequisites

- Docker Desktop running
- Repo cloned, no additional secrets required (demo uses static local credentials only, per
  constitution scope — no real auth/PII)

## Bring up the platform

```powershell
docker compose up -d
```

This starts MinIO, Redpanda, Postgres, Airflow, the streaming producer/consumer, and Metabase —
one command, per FR-010/SC-004.

## Validate User Story 1 — Historical Trend Review

1. Wait for the Airflow webserver to report healthy, then confirm `batch_load_dag` has run
   (scheduled on startup) — this generates and loads the ~50,000-transaction historical dataset
   and runs `dbt run`.
2. Open Metabase and view the "FinPulse Overview" dashboard (auto-provisioned by
   `infra/metabase/provision_dashboard.py`).
3. **Expected**: transaction volume over time and revenue-by-merchant/region charts are populated,
   within 15 minutes of step 1 (spec SC-001).

## Validate User Story 2 — Fraud Risk Visibility

1. Confirm `fraud_scoring_dag` has run after `batch_load_dag`.
2. **Expected**: the dashboard's flagged-transaction-rate KPI shows a non-null value, and every
   row in `fct_fraud_scores` has a `risk_score` (spec SC-003 — 100% of transactions scored).

## Validate User Story 3 — Live Activity Monitoring

1. With the platform already running, note the current transaction volume figure on the
   dashboard.
2. Wait 5 minutes (the streaming producer is continuously emitting ~5 transactions/sec).
3. Refresh the dashboard.
4. **Expected**: transaction volume has increased, and the flagged-transaction-rate KPI reflects
   any newly-flagged streamed transactions — with no distinction visible to the analyst between
   batch- and streaming-sourced data (spec SC-002).

## Tear down

```powershell
docker compose down -v
```
