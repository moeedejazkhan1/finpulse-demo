# Phase 1 Data Model: FinPulse Transaction Analytics Platform

Entities correspond to the Key Entities in [spec.md](./spec.md). This shape is the shared schema
referenced by constitution Principle II (batch and streaming land in the same raw zone using one
schema) and is formalized as a contract in
[contracts/transaction-event-schema.md](./contracts/transaction-event-schema.md).

## Account

Represents a synthetic bank account holder.

| Field | Type | Notes |
|---|---|---|
| `account_id` | string (UUID) | Primary key |
| `opened_at` | timestamp | Account creation date, synthetic |
| `region` | string | One of a fixed set of demo regions (e.g., US-East, US-West, EU, APAC) |

## Merchant

Represents a business receiving transaction payments.

| Field | Type | Notes |
|---|---|---|
| `merchant_id` | string (UUID) | Primary key |
| `name` | string | Synthetic business name |
| `category` | string | e.g., grocery, travel, electronics, dining |
| `region` | string | Same fixed region set as Account |

## Transaction

A single payment event between an account and a merchant. This is the entity that flows through
both the batch and streaming paths using an identical shape.

| Field | Type | Notes |
|---|---|---|
| `transaction_id` | string (UUID) | Primary key; generated at source so batch/streaming collisions are negligible |
| `account_id` | string (UUID) | FK → Account |
| `merchant_id` | string (UUID) | FK → Merchant |
| `amount` | decimal | Must be > 0 |
| `currency` | string | Fixed to `USD` for demo simplicity |
| `occurred_at` | timestamp | When the transaction happened; must be ≤ `ingested_at` |
| `source` | enum | `batch` \| `streaming` |
| `ingested_at` | timestamp | System-assigned on landing in the raw zone |

**Validation rules**:
- `amount` > 0
- `occurred_at` ≤ `ingested_at`
- `source` ∈ {`batch`, `streaming`}
- `transaction_id` unique across both sources (see Edge Cases in spec.md — dedup on primary key
  during staging if a collision ever occurs)

## Fraud Risk Score

A derived record produced by the batch scoring step, one-to-one with Transaction, materialized in
the marts layer as `fct_fraud_scores` (kept separate from `fct_transactions` per the Constitution
Check rationale in plan.md — enrichment output, not dbt transformation output).

| Field | Type | Notes |
|---|---|---|
| `transaction_id` | string (UUID) | FK → Transaction (1:1) |
| `risk_score` | float | Range 0.0–1.0; IsolationForest anomaly score, normalized |
| `is_flagged` | boolean | Derived from a threshold on `risk_score` |
| `scored_at` | timestamp | When the scoring job produced this record |

## Lifecycle (not a formal state machine)

A transaction has an implicit pipeline lifecycle rather than an explicit status field:

`generated/received → landed in raw (MinIO) → staged (dbt) → in marts (dbt) → scored (ML job) →
visible on dashboard (Metabase)`

Every stage is idempotent and re-runnable per constitution Principle IV — no stage depends on
in-memory state from a prior run.
