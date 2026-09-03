# FinPulse — Project Constitution

## Purpose
A demo data platform showing a full-stack financial-transactions analytics
pipeline: batch + streaming ingestion, warehouse modeling, fraud-signal ML
scoring, and a BI dashboard. Built to demonstrate solution architecture
capability to an incoming client — patterns here should generalize to their
real domain, not stay hardcoded to "finance."

## Scope
IN SCOPE:
- Synthetic financial transaction data (accounts, transactions, merchants)
- Batch historical load + simulated real-time transaction stream
- Warehouse modeling using a bronze/silver/gold (raw/staging/marts) layering
- A simple anomaly/fraud-signal scoring model, batch-applied
- A BI dashboard surfacing core KPIs

OUT OF SCOPE (for this demo):
- Production-grade security/auth, PII handling, regulatory compliance
- Multi-tenant or high-availability infrastructure
- Real payment processor integration

## Locked technology decisions
- Orchestration: Airflow
- Object/raw storage: MinIO (S3-compatible, local)
- Streaming: Redpanda (Kafka-compatible, lighter footprint)
- Warehouse: Postgres
- Transformation: dbt
- ML: scikit-learn, batch scoring (no real-time inference in v1)
- BI: Metabase
- All services run locally via Docker Compose — no cloud account required

## Architecture principles
1. Medallion layering: raw → staging (cleaned/typed) → marts (business-ready)
2. Batch and streaming both land in the same raw zone before transformation —
   one transformation layer serves both paths
3. Every transformation is defined in dbt, not ad-hoc scripts — models are the
   single source of truth for business logic
4. Every pipeline component must be independently runnable/testable
5. Optimize for demo clarity over production hardening — this is a reference
   architecture, not a production system

## Definition of done (for the demo)
- `docker compose up` brings up the full stack from a clean checkout
- Historical batch data flows raw → marts automatically via Airflow
- Simulated streaming transactions land in raw and flow through the same
  models within a scheduled interval
- Fraud-signal scores appear on transactions in the gold layer
- Metabase dashboard shows: transaction volume over time, revenue by
  merchant/region, flagged-transaction rate
