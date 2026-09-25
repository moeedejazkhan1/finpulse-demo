# FinPulse

A demo financial-transactions analytics platform, built end-to-end using a
**Spec-Driven Development (SDD)** approach via [GitHub Spec Kit](https://github.com/github/spec-kit).
Every requirement, architecture decision, and task was written down and
reviewed before any code existed — see `specs/001-transaction-analytics/`
for the full trail: `constitution.md` (via `.specify/memory/`) → `spec.md`
→ `plan.md` → `tasks.md`.

This build implements **Setup, Foundational, User Story 1 (Historical
Trend Review), and User Story 2 (Fraud Risk Visibility)** — tasks
T001–T024. Live streaming (User Story 3) is out of scope for this pass.

## What it does

- Generates a synthetic historical dataset (~500 accounts, ~200 merchants,
  ~50,000 transactions) and lands it in a MinIO raw zone + Postgres
- Transforms it through dbt (staging → marts) into a business-ready model
- Scores every transaction for fraud risk with an IsolationForest model
- Serves a Metabase dashboard: transaction volume over time, revenue by
  merchant/region, and the flagged-transaction rate
- Orchestrates all of the above with Airflow — one `docker compose up`
  brings the whole thing up unattended

## Prerequisites

- Docker Desktop (with WSL2 backend on Windows), running
- ~4GB free RAM for the stack (Postgres, MinIO, 2x Airflow, Metabase)

## Run it

```powershell
docker compose up -d --build
```

First boot takes a few minutes (Airflow migrates its metadata DB, Metabase
does initial setup). Then trigger the two DAGs — either from the Airflow
UI (http://localhost:8080, admin/admin) or:

```powershell
docker compose exec airflow-webserver airflow dags trigger batch_load_dag
# wait for it to finish, then:
docker compose exec airflow-webserver airflow dags trigger fraud_scoring_dag
```

Or just run `scripts\validate-clean-checkout.ps1`, which does all of the
above and waits for you.

## See it

| Service | URL | Login |
|---|---|---|
| Metabase dashboard | http://localhost:3000 | admin@finpulse.local / FinPulseDemo123! |
| Airflow | http://localhost:8080 | admin / admin |
| MinIO console (raw zone) | http://localhost:9001 | finpulse / finpulse123 |

The **FinPulse Overview** dashboard in Metabase is provisioned automatically
— no manual dashboard building — by `infra/metabase/provision_dashboard.py`,
which runs once via the `metabase-init` service.

## Run the tests

```powershell
pip install -e ".[dev]"
pytest tests/unit tests/contract -v          # no stack required
pytest tests/integration -v                  # requires the stack to be up
```

## Tear down

```powershell
docker compose down -v
```

## Running without Docker

If Docker isn't available (no admin rights, no WSL2), the full pipeline also runs as native
Windows processes — see the constitution's **Deployment Environment Exception** (v1.1.0) for why
this exists and what it changes (Airflow → a plain script; MinIO → `moto`'s S3-compatible mock
server, since MinIO stopped shipping Windows binaries).

```powershell
# One-time: portable Postgres + Java + Metabase downloaded into runtime/ (gitignored)
# and a Python 3.11 venv (.venv311) with dbt-postgres installed (Python 3.14 lacks
# prebuilt wheels for some deps as of this writing).

# 1. Start Postgres (extracts + initializes on first run)
powershell -File scripts\native\setup-postgres.ps1

# 2. Start the S3-compatible mock server (separate terminal, leave running)
.venv311\Scripts\python.exe scripts\native\start-s3-mock.py

# 3. Run the pipeline (generate -> land -> dbt run -> score)
.venv311\Scripts\python.exe scripts\run_pipeline.py

# 4. Start Metabase (separate terminal, leave running; first boot ~1-2 min)
powershell -File scripts\native\start-metabase.ps1

# 5. Once Metabase is up, provision the dashboard
powershell -File scripts\native\provision-dashboard.ps1
```

Same URLs as the Docker path (Postgres on 5432, S3-mock on 9000, Metabase on 3000) — just no
`docker compose`, no Airflow UI. Re-running `run_pipeline.py` appends a fresh batch (new random
UUIDs each time) rather than replacing data, which is fine for a demo but worth knowing.
