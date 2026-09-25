---
description: "Task list for FinPulse Transaction Analytics Platform"
---

# Tasks: FinPulse Transaction Analytics Platform

**Input**: Design documents from `/specs/001-transaction-analytics/`

**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/transaction-event-schema.md, quickstart.md

**Tests**: Contract and integration tests are included (Phase 6) since the shared batch/streaming
schema contract is a constitution-level requirement (Principle II), not optional polish.

**Organization**: Tasks are grouped by user story (P1/P2/P3 from spec.md) so each phase ends in an
independently demoable increment.

**Build status (2026-09-25)**: T001–T024 and the adapted Polish tasks (T031–T034) are implemented.
Phase 5 (User Story 3 / streaming) was descoped for this build by explicit architect decision —
see the note on Phase 5 below. Final `docker compose up` validation is pending Docker Desktop
being installed on the demo machine.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no unmet dependency)
- **[Story]**: Which user story this task belongs to (US1, US2, US3)

## Path Conventions

Single local data-platform project (see plan.md Project Structure) — `src/`, `dbt/`, `airflow/`,
`infra/`, `tests/`, `docker-compose.yml` at repository root.

---

## Phase 1: Setup

**Purpose**: Repo scaffolding shared by every story

- [X] T001 Create the directory skeleton per plan.md: `src/common/`, `src/datagen/`,
      `src/streaming/producer/`, `src/streaming/consumer/`, `src/ml/fraud_scoring/`, `dbt/`,
      `airflow/dags/`, `infra/{minio,redpanda,postgres,metabase}/`,
      `tests/{unit,contract,integration}/`
- [X] T002 Create `docker-compose.yml` skeleton at repo root defining `postgres`, `minio`,
      `redpanda`, `airflow-webserver`, `airflow-scheduler`, and `metabase` services with
      healthchecks (no application logic wired in yet)
- [X] T003 [P] Add Python dependency manifest (`pyproject.toml`) pinning `faker`, `boto3`,
      `confluent-kafka`, `scikit-learn`, `pandas`, `pytest`, `dbt-postgres`
- [X] T004 [P] Configure `ruff`/`black` for `src/` and `tests/`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Infrastructure every user story depends on

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T005 [P] Implement the shared Account/Merchant/Transaction schema (dataclasses or Pydantic
      models) in `src/common/schema.py`, matching
      `specs/001-transaction-analytics/contracts/transaction-event-schema.md` and
      `data-model.md` exactly, including validation rules (`amount > 0`,
      `occurred_at <= ingested_at`, `source` ∈ {batch, streaming})
- [X] T006 [P] Add Postgres init script in `infra/postgres/` creating the `finpulse` (warehouse)
      and `airflow` (metadata) databases in the same instance, per research.md
- [X] T007 [P] Add MinIO startup script in `infra/minio/` that creates the `finpulse-raw` bucket
      used by both the batch and streaming paths
- [X] T008 Initialize the dbt project skeleton in `dbt/` (`dbt_project.yml`, `profiles.yml`
      pointed at the `finpulse` Postgres database, empty `models/staging/` and `models/marts/`,
      and a source definition for the MinIO-landed raw data) — depends on T006
- [X] T009 Initialize Airflow config in `airflow/` referencing `airflow/dags/` and using the
      `airflow` database from T006 as its metadata store — depends on T006

**Checkpoint**: Foundation ready — user story phases can begin.

---

## Phase 3: User Story 1 - Historical Trend Review (Priority: P1) 🎯 MVP

**Goal**: Batch-loaded historical data flows through to a dashboard showing volume over time and
revenue by merchant/region. Satisfies SC-001.

**Independent Test**: Run only the batch path (no streaming, no scoring) end-to-end and confirm
the dashboard is populated within 15 minutes of a clean `docker compose up`.

- [X] T010 [P] [US1] Implement synthetic account/merchant generation (~500 accounts, ~200
      merchants) in `src/datagen/generate.py`, using `src/common/schema.py` — depends on T005
- [X] T011 [P] [US1] Implement synthetic historical transaction generation (~50,000 transactions,
      `source="batch"`) in `src/datagen/generate.py`, using `src/common/schema.py` — depends on
      T005
- [X] T012 [US1] Implement the batch loader that writes generated accounts/merchants/transactions
      as newline-delimited JSON into the `finpulse-raw` MinIO bucket — depends on T007, T010, T011
- [X] T013 [P] [US1] Create dbt staging models (`stg_accounts`, `stg_merchants`,
      `stg_transactions`) in `dbt/models/staging/` reading the MinIO-sourced raw data — depends on
      T008
- [X] T014 [US1] Create dbt marts models (`fct_transactions`, `dim_account`, `dim_merchant`) in
      `dbt/models/marts/` supporting volume-over-time and revenue-by-merchant/region aggregation —
      depends on T013
- [X] T015 [US1] Implement `airflow/dags/batch_load_dag.py` orchestrating generate → load to
      MinIO → `dbt run` (staging + marts), scheduled to run on startup — depends on T012, T014
- [X] T016 [P] [US1] Write version-controlled Metabase question/dashboard definitions (volume over
      time, revenue by merchant/region) as JSON in `infra/metabase/`
- [X] T017 [US1] Implement `infra/metabase/provision_dashboard.py`, calling the Metabase REST API
      on first boot to create the Postgres connection and the dashboard from T016 — depends on
      T016
- [X] T018 [US1] Wire `batch_load_dag`, dbt, and Metabase provisioning into `docker-compose.yml`
      so `docker compose up` runs the full US1 path — depends on T002, T015, T017

**Checkpoint**: US1 is independently demoable — SC-001 is satisfiable.

---

## Phase 4: User Story 2 - Fraud Risk Visibility (Priority: P2)

**Goal**: Every transaction gets a fraud-risk score, surfaced as a flagged-transaction-rate KPI.
Satisfies SC-003.

**Independent Test**: With US1's data already loaded and modeled, run the scoring job standalone
and confirm every transaction receives a score and the dashboard KPI reflects it.

- [X] T019 [P] [US2] Implement feature extraction (amount, time-of-day, merchant category,
      account velocity) in `src/ml/fraud_scoring/features.py`, reading from `fct_transactions` —
      depends on T014
- [X] T020 [US2] Implement `IsolationForest` batch scoring in `src/ml/fraud_scoring/score.py`,
      producing `risk_score` + `is_flagged` per transaction and writing to a new
      `fct_fraud_scores` table in Postgres — depends on T019
- [X] T021 [US2] Add a dbt source/marts definition for `fct_fraud_scores` in
      `dbt/models/marts/` so it's queryable alongside `fct_transactions` — depends on T020
- [X] T022 [US2] Implement `airflow/dags/fraud_scoring_dag.py` orchestrating `dbt run`
      (incremental) → `src/ml/fraud_scoring/score.py`, scheduled after `batch_load_dag` — depends
      on T015, T020
- [X] T023 [P] [US2] Add the flagged-transaction-rate question/card to the Metabase definitions in
      `infra/metabase/` — depends on T016, T021
- [X] T024 [US2] Wire `fraud_scoring_dag` into the `docker-compose.yml` startup sequence —
      depends on T018, T022, T023

**Checkpoint**: US1 + US2 both independently demoable — SC-003 is satisfiable.

---

## Phase 5: User Story 3 - Live Activity Monitoring (Priority: P3)

**⏸ Descoped for this build** (architect decision, 2026-09-25): the demo for this milestone is
scoped to MVP + fraud scoring only. Streaming adds Redpanda setup/debugging risk that wasn't
worth the time against the demo deadline. Revisit after T001–T024/T031–T034 are validated live.

**Goal**: Simulated real-time transactions land, model, score, and appear on the dashboard within
a bounded refresh window. Satisfies SC-002.

**Independent Test**: With US1 + US2 already running, start the streaming simulator and confirm
new transactions reach the dashboard's KPIs within the defined interval, through the same models
as batch data.

- [ ] T025 [P] [US3] Add the Redpanda service to `docker-compose.yml` with the transaction topic
      auto-created on startup — depends on T002
- [ ] T026 [P] [US3] Implement the streaming producer in `src/streaming/producer/producer.py`,
      emitting ~5 synthetic transactions/sec (`source="streaming"`) using `src/common/schema.py` —
      depends on T005, T025
- [ ] T027 [US3] Implement the streaming consumer in `src/streaming/consumer/consumer.py`, reading
      the Redpanda topic and landing transactions into the same `finpulse-raw` bucket/prefix used
      by the batch path — depends on T007, T025, T026
- [ ] T028 [US3] Add a short-interval scheduled trigger for the staging/marts `dbt run` step so
      newly-landed streaming records are picked up within the 5-minute freshness window — depends
      on T015, T027
- [ ] T029 [US3] Confirm `fraud_scoring_dag`'s schedule also covers newly-streamed transactions
      within the same interval, so streamed data gets scored like batch data — depends on T022,
      T028
- [ ] T030 [US3] Wire the streaming producer/consumer into `docker-compose.yml` so they start
      automatically with `docker compose up` — depends on T024, T026, T027

**Checkpoint**: All three user stories independently functional — full spec.md scope is
demoable.

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Validate the constitution's Definition of Done and the shared-schema contract

- [X] T031 [P] Contract tests in `tests/contract/test_transaction_schema.py` — **scoped to the
      batch path only** (no streaming producer exists in this build) — validating `src/datagen`
      output conforms to `contracts/transaction-event-schema.md` — depends on T011
- [X] T032 [P] Unit tests for the feature-extraction logic in
      `tests/unit/test_fraud_scoring.py` — depends on T020
- [X] T033 Integration/smoke test in `tests/integration/test_end_to_end.py` validating SC-001 and
      SC-003 against a live stack (skips cleanly if the stack isn't up) — depends on T018, T024
- [X] T034 `scripts/validate-clean-checkout.ps1` automates a full clean-checkout run
      (`docker compose down -v` → `up -d --build` → trigger both DAGs) — depends on T033.
      **Not yet executed**: pending Docker Desktop install on the demo machine.

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: no dependencies
- **Foundational (Phase 2)**: depends on Setup — blocks all user stories
- **User Story 1 (Phase 3)**: depends on Foundational only
- **User Story 2 (Phase 4)**: depends on Foundational + US1's `fct_transactions` (T014) and
  Metabase scaffolding (T016) — not independently buildable before US1, but independently
  *demoable* once built
- **User Story 3 (Phase 5)**: depends on Foundational + US1's DAG/loading pattern (T015) and
  MinIO bucket (T007) — likewise builds on US1's scaffolding but is independently demoable.
  **Descoped for this build — see note above.**
- **Polish (Phase 6)**: depends on the implemented user stories being complete (US1 + US2 here)

### Parallel Opportunities

- T003, T004 (Setup) in parallel
- T005, T006, T007 (Foundational) in parallel
- T010, T011 (US1 data generation) in parallel; T013, T016 in parallel with each other
- T019 (US2) can start as soon as T014 lands, in parallel with remaining US1 polish tasks
- T025, T026 (US3) in parallel — not built in this pass
- T031, T032 (Polish) in parallel

---

## Parallel Example: User Story 1

```bash
# After Foundational (Phase 2) completes:
Task: "Implement synthetic account/merchant generation in src/datagen/generate.py"
Task: "Implement synthetic historical transaction generation in src/datagen/generate.py"
Task: "Write Metabase question/dashboard definitions in infra/metabase/"
```

---

## Implementation Strategy

### MVP First (User Story 1 only)

1. Complete Phase 1 (Setup) + Phase 2 (Foundational)
2. Complete Phase 3 (US1)
3. **STOP and VALIDATE**: run `quickstart.md`'s US1 validation, confirm SC-001
4. This alone is a demoable artifact for the client

### Incremental Delivery

1. Setup + Foundational → foundation ready
2. + US1 → demo the batch pipeline + dashboard (MVP) ✅ built
3. + US2 → demo fraud-risk scoring on top ✅ built
4. + US3 → demo live streaming freshness on top — descoped for this build
5. + Polish → contract/integration tests ✅ built; full clean-checkout validation pending Docker
