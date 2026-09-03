# Phase 0 Research: FinPulse Transaction Analytics Platform

All Technical Context fields were resolvable from the ratified constitution's locked stack, so
research here focuses on integration/best-practice decisions rather than open unknowns.

## Streaming client for Redpanda

- **Decision**: `confluent-kafka` (librdkafka-based Python client)
- **Rationale**: Redpanda is Kafka-API-compatible; `confluent-kafka` is the most widely used,
  best-performing, and best-documented client against that API, minimizing integration risk for a
  demo that needs to run reliably during a client presentation.
- **Alternatives considered**: `kafka-python` (pure Python, less actively maintained, materially
  slower) — rejected for demo reliability.

## Fraud-risk scoring approach

- **Decision**: scikit-learn `IsolationForest` (unsupervised anomaly detection) over transaction
  features (amount, time-of-day, merchant category, account velocity).
- **Rationale**: synthetic demo data has no ground-truth fraud labels, so a supervised classifier
  has nothing real to learn from. `IsolationForest` produces a defensible anomaly/risk score
  without needing labeled data, which is sufficient to demonstrate the ML plumbing end-to-end —
  matching constitution Principle V (demo clarity over production rigor; this is not a validated
  fraud model).
- **Alternatives considered**: inject synthetic labeled fraud patterns + a supervised classifier
  (logistic regression / gradient boosting) — rejected as unnecessary complexity; the demo's goal
  is to prove the batch-scoring architecture, not fraud-detection accuracy.

## Airflow metadata database

- **Decision**: reuse the same Postgres container/instance as the warehouse, in a separate
  database (`airflow`) from the warehouse database (`finpulse`).
- **Rationale**: minimizes the number of moving parts in `docker-compose.yml`, consistent with
  constitution Principle V. Airflow's metadata and the warehouse data are logically distinct via
  separate databases, so there is no risk of cross-contamination.
- **Alternatives considered**: a dedicated Postgres instance for Airflow — rejected as an
  unnecessary extra container for a local demo.

## MinIO access pattern

- **Decision**: `boto3` S3 client configured with MinIO's local endpoint URL and static demo
  credentials.
- **Rationale**: `boto3` is the de facto standard S3 client; using it keeps the ingestion code
  portable to a real S3 bucket later with only a config change, which is a natural talking point
  for the client demo.
- **Alternatives considered**: MinIO's native Python SDK — rejected; `boto3` is more broadly known
  and better documented for a solution-architecture audience.

## Metabase dashboard provisioning

- **Decision**: a startup script (`infra/metabase/provision_dashboard.py`) calls Metabase's REST
  API on first boot to create the Postgres connection, saved questions, and dashboard from
  version-controlled JSON definitions.
- **Rationale**: the constitution's Definition of Done requires the dashboard to appear from a
  single `docker compose up` with no manual steps (FR-010/SC-004). API-driven provisioning from
  files in the repo is reviewable in git diffs and reproducible on a second machine.
- **Alternatives considered**: shipping a pre-built Metabase application-database file — rejected
  as an opaque binary artifact, hard to review or diff, and brittle across Metabase versions.

## Synthetic data generation

- **Decision**: `Faker` (Python) for account/merchant names, regions, and realistic transaction
  timestamps/amounts.
- **Rationale**: standard, well-maintained library purpose-built for exactly this; avoids
  reinventing realistic-looking synthetic data generation.
- **Alternatives considered**: hand-rolled random generation — rejected as unnecessary effort for
  a solved problem.
