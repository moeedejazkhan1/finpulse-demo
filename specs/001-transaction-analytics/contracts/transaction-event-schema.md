# Contract: Transaction Event Schema

This is the one shared schema that both the batch loader (`src/datagen` → MinIO raw) and the
streaming path (`src/streaming/producer` → Redpanda → `src/streaming/consumer` → MinIO raw) MUST
produce, per constitution Principle II (Unified Transformation Path). dbt's staging models assume
this exact shape regardless of which path a record came from — a divergence here is a contract
break, not a normal bug.

## Record shape (JSON)

```json
{
  "transaction_id": "uuid-string",
  "account_id": "uuid-string",
  "merchant_id": "uuid-string",
  "amount": "decimal string or number, > 0",
  "currency": "USD",
  "occurred_at": "ISO-8601 timestamp",
  "source": "batch | streaming",
  "ingested_at": "ISO-8601 timestamp, set by the loader/consumer, not the generator"
}
```

## Producer responsibilities

| Path | Sets `source` to | Writes to |
|---|---|---|
| Batch loader (`src/datagen` via `airflow/dags/batch_load_dag.py`) | `"batch"` | MinIO raw zone, as newline-delimited JSON files |
| Streaming consumer (`src/streaming/consumer`) | `"streaming"` | MinIO raw zone, same bucket/prefix convention as batch |

Both paths write into the **same MinIO bucket/prefix structure** so a single dbt source
definition covers both — this is the mechanism, not just the intent, behind Principle II.

## Consumer responsibilities (dbt staging models)

- MUST accept records from either `source` value with no branching transformation logic — the
  staging model applies identical typing/cleaning regardless of `source`.
- MUST treat `source` as a pass-through attribute available in marts (used to answer, e.g., "how
  much of current volume is from live streaming vs. historical load"), not as a switch that
  changes business logic.

## Versioning

This is the v1 contract for the FinPulse demo. Any field addition, rename, or type change here
requires updating this file, `data-model.md`, and re-validating both producers before merging —
this file is the source of truth both producers are tested against (`tests/contract/`).
