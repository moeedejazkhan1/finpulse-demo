# Implementation Plan: FinPulse Transaction Analytics Platform

**Branch**: `001-transaction-analytics` | **Date**: 2026-09-03 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `/specs/001-transaction-analytics/spec.md`

## Summary

Build a local, fully-Dockerized data platform that ingests synthetic financial transactions via
both a historical batch load and a simulated real-time stream, transforms both through one shared
dbt medallion pipeline (raw → staging → marts) in Postgres, applies a batch fraud-risk scoring
step, and surfaces the result as a Metabase dashboard (volume over time, revenue by
merchant/region, flagged-transaction rate). Airflow orchestrates batch load and scoring on a
schedule; MinIO and Redpanda provide raw storage and streaming transport respectively — all per
the ratified constitution's locked stack.

## Technical Context

**Language/Version**: Python 3.11 (data generator, streaming producer/consumer, ML scoring job)

**Primary Dependencies**: Apache Airflow, dbt-postgres, confluent-kafka (Redpanda client), boto3
(MinIO/S3 client), scikit-learn, pandas, Faker

**Storage**: MinIO (raw zone, S3-compatible) for landed batch/streaming data; Postgres for
staging/marts (dbt-managed) and Airflow metadata

**Testing**: pytest (datagen, streaming, ML scoring unit/contract tests), dbt test (staging/marts
model tests)

**Target Platform**: Local Docker Compose stack (Linux containers, Docker Desktop on the
architect's Windows machine)

**Project Type**: Local multi-service data platform (batch + streaming pipeline, not a
client/server app or mobile app)

**Performance Goals**: Streaming consumer keeps pace with ~5 transactions/sec with the new data
visible on the dashboard within 5 minutes (spec SC-002); full historical batch (~50,000
transactions) loaded, modeled, scored, and dashboard-visible within 15 minutes of a clean
`docker compose up` (spec SC-001)

**Constraints**: Fully local, no cloud account required; single `docker compose up` startup with
zero manual per-service configuration (spec FR-010/SC-004); demo-scale data only

**Scale/Scope**: ~50,000 historical transactions, ~500 synthetic accounts, ~200 synthetic
merchants, ~5 transactions/sec simulated streaming, single-node local deployment, single dashboard
consumed by one analyst persona

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-checked after Phase 1 design.*

| Principle | Check | Result |
|---|---|---|
| I. Medallion Data Layering | Raw (MinIO) → staging → marts (Postgres, dbt-managed); no component writes directly to marts | PASS |
| II. Unified Transformation Path | Batch loader and streaming consumer both write into the same raw zone/schema before dbt runs; one dbt project models both | PASS |
| III. dbt as Single Source of Transformation Truth | All business-logic transformation is dbt models; the ML scoring job is an explicit *enrichment* step that reads dbt-produced marts and writes scores back — it does not perform transformation logic itself | PASS (see rationale below) |
| IV. Independent Component Testability | `src/datagen`, `src/streaming`, `src/ml`, `dbt/`, and `airflow/` are each independently runnable/testable (see Project Structure) | PASS |
| V. Demo Clarity Over Production Hardening | No auth, multi-tenancy, or HA introduced; Metabase/Airflow run with default local-only settings | PASS |

**Rationale for Principle III interpretation**: the constitution requires dbt to be the single
source of truth for *transformation* (raw → staging → marts). Fraud scoring is not a
transformation of existing fields but a new derived signal requiring a model inference step,
which dbt cannot execute natively. It is scoped as a distinct, clearly-bounded enrichment stage
that consumes dbt's output and writes to its own marts table (`fct_fraud_scores`), keeping the
transformation/enrichment boundary explicit rather than blurring ad-hoc logic into dbt or
bypassing dbt entirely.

**Initial Constitution Check**: PASS (no violations; Complexity Tracking not required)
**Post-Design Constitution Check** (after Phase 1 artifacts below): PASS — data model and
contracts introduce no new components or coupling that would change the table above.

## Project Structure

### Documentation (this feature)

```text
specs/001-transaction-analytics/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md         # Phase 1 output
├── quickstart.md         # Phase 1 output
├── contracts/             # Phase 1 output
│   └── transaction-event-schema.md
└── tasks.md               # Phase 2 output (/speckit-tasks — not created here)
```

### Source Code (repository root)

```text
src/
├── common/                 # Shared schema/validation used by both datagen and streaming
│   └── schema.py
├── datagen/                 # Synthetic account/merchant/transaction generator (batch seed)
│   └── generate.py
├── streaming/
│   ├── producer/             # Simulates ~5 txn/sec onto the Redpanda topic
│   │   └── producer.py
│   └── consumer/             # Reads Redpanda, lands transactions into MinIO raw zone
│       └── consumer.py
└── ml/
    └── fraud_scoring/         # scikit-learn batch scoring job (IsolationForest)
        └── score.py

dbt/
├── models/
│   ├── staging/               # Cleaned/typed, one model per raw entity
│   └── marts/                 # Business-ready marts, incl. fct_fraud_scores
├── dbt_project.yml
└── profiles.yml

airflow/
└── dags/
    ├── batch_load_dag.py      # datagen (batch) -> MinIO raw -> dbt run
    └── fraud_scoring_dag.py   # dbt run (incremental) -> ML scoring -> fct_fraud_scores

infra/
├── minio/
├── redpanda/
├── postgres/
└── metabase/
    └── provision_dashboard.py # Scripts Metabase's REST API to create the connection + dashboard

docker-compose.yml              # Repo root — single entry point per FR-010/SC-004

data/                            # Generated synthetic data (gitignored)

tests/
├── unit/                        # datagen, ML scoring
├── contract/                    # Shared batch/streaming schema conformance
└── integration/                 # dbt tests, end-to-end pipeline smoke test
```

**Structure Decision**: Organized by pipeline stage rather than by a single app/library layout,
since this is a multi-service data platform, not a client/server or mobile app — none of the
template's default options fit directly. Each top-level directory (`src/*`, `dbt/`, `airflow/`)
is independently runnable and testable per constitution Principle IV. `docker-compose.yml` lives
at the repo root so `docker compose up` (FR-010) has one unambiguous entry point; per-service
config lives under `infra/<service>/`.

## Complexity Tracking

*No Constitution Check violations — this section is not applicable.*
