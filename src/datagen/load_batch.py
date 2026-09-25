"""Batch loader (T012): lands generated data in MinIO (raw zone) and
loads it into Postgres raw schema tables that dbt's staging models
source from.

MinIO holds the immutable, replayable landing copy (the actual "raw
zone" per the constitution). Postgres raw.* tables are the queryable
raw layer -- dbt-postgres cannot read object storage directly, so this
loader is the bridge between the two, consistent with plan.md.
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import uuid
from pathlib import Path

import boto3
import psycopg2
import psycopg2.extras

RAW_BUCKET = "finpulse-raw"


def s3_client():
    return boto3.client(
        "s3",
        endpoint_url=os.environ.get("MINIO_ENDPOINT", "http://localhost:9000"),
        aws_access_key_id=os.environ.get("MINIO_ROOT_USER", "finpulse"),
        aws_secret_access_key=os.environ.get("MINIO_ROOT_PASSWORD", "finpulse123"),
    )


def pg_connect():
    return psycopg2.connect(
        host=os.environ.get("POSTGRES_HOST", "localhost"),
        port=os.environ.get("POSTGRES_PORT", "5432"),
        dbname=os.environ.get("POSTGRES_DB", "finpulse"),
        user=os.environ.get("POSTGRES_USER", "finpulse"),
        password=os.environ.get("POSTGRES_PASSWORD", "finpulse"),
    )


def upload_to_minio(client, local_path: Path, entity: str, batch_id: str, ingest_date: str) -> None:
    key = f"{entity}/ingest_date={ingest_date}/{batch_id}.ndjson"
    client.upload_file(str(local_path), RAW_BUCKET, key)
    print(f"  uploaded s3://{RAW_BUCKET}/{key}")


def load_accounts(cur, path: Path, batch_id: str) -> int:
    rows = []
    with path.open(encoding="utf-8") as f:
        for line in f:
            r = json.loads(line)
            rows.append((r["account_id"], r["opened_at"], r["region"], batch_id))
    psycopg2.extras.execute_values(
        cur,
        """
        INSERT INTO raw.accounts (account_id, opened_at, region, _batch_id)
        VALUES %s
        ON CONFLICT (account_id) DO NOTHING
        """,
        rows,
    )
    return len(rows)


def load_merchants(cur, path: Path, batch_id: str) -> int:
    rows = []
    with path.open(encoding="utf-8") as f:
        for line in f:
            r = json.loads(line)
            rows.append((r["merchant_id"], r["name"], r["category"], r["region"], batch_id))
    psycopg2.extras.execute_values(
        cur,
        """
        INSERT INTO raw.merchants (merchant_id, name, category, region, _batch_id)
        VALUES %s
        ON CONFLICT (merchant_id) DO NOTHING
        """,
        rows,
    )
    return len(rows)


def load_transactions(cur, path: Path, batch_id: str) -> int:
    rows = []
    with path.open(encoding="utf-8") as f:
        for line in f:
            r = json.loads(line)
            rows.append(
                (
                    r["transaction_id"],
                    r["account_id"],
                    r["merchant_id"],
                    r["amount"],
                    r["currency"],
                    r["occurred_at"],
                    r["source"],
                    r["ingested_at"],
                    batch_id,
                )
            )
    psycopg2.extras.execute_values(
        cur,
        """
        INSERT INTO raw.transactions
            (transaction_id, account_id, merchant_id, amount, currency,
             occurred_at, source, ingested_at, _batch_id)
        VALUES %s
        ON CONFLICT (transaction_id) DO NOTHING
        """,
        rows,
    )
    return len(rows)


def main() -> None:
    parser = argparse.ArgumentParser(description="Land generated batch data into MinIO + Postgres")
    parser.add_argument("--data-dir", default="data/batch")
    args = parser.parse_args()

    data_dir = Path(args.data_dir)
    batch_id = f"bl_{uuid.uuid4().hex[:12]}"
    ingest_date = dt.date.today().isoformat()

    print(f"batch_id={batch_id}")

    s3 = s3_client()
    accounts_path = data_dir / "accounts" / "accounts.ndjson"
    merchants_path = data_dir / "merchants" / "merchants.ndjson"
    transactions_path = data_dir / "transactions" / "transactions.ndjson"

    upload_to_minio(s3, accounts_path, "accounts", batch_id, ingest_date)
    upload_to_minio(s3, merchants_path, "merchants", batch_id, ingest_date)
    upload_to_minio(s3, transactions_path, "transactions", batch_id, ingest_date)

    conn = pg_connect()
    try:
        with conn.cursor() as cur:
            n_accounts = load_accounts(cur, accounts_path, batch_id)
            n_merchants = load_merchants(cur, merchants_path, batch_id)
            n_transactions = load_transactions(cur, transactions_path, batch_id)
        conn.commit()
    finally:
        conn.close()

    print(
        f"loaded into postgres raw schema: {n_accounts} accounts, "
        f"{n_merchants} merchants, {n_transactions} transactions"
    )


if __name__ == "__main__":
    main()
