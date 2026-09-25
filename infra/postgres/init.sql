-- Runs automatically on first container start (mounted into
-- /docker-entrypoint-initdb.d/ by docker-compose.yml).
-- Creates the warehouse database and a separate database for Airflow's
-- own metadata, per research.md's "reuse one Postgres instance" decision.

CREATE DATABASE airflow;

\connect finpulse

CREATE SCHEMA IF NOT EXISTS raw;
CREATE SCHEMA IF NOT EXISTS staging;
CREATE SCHEMA IF NOT EXISTS marts;

-- Raw layer tables. Loaded by src/datagen's batch loader from the
-- newline-delimited JSON files it also lands in MinIO (the immutable
-- raw zone). dbt's staging models source from these tables.

CREATE TABLE IF NOT EXISTS raw.accounts (
    account_id   TEXT PRIMARY KEY,
    opened_at    TIMESTAMPTZ NOT NULL,
    region       TEXT NOT NULL,
    _batch_id    TEXT NOT NULL,
    _ingested_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS raw.merchants (
    merchant_id  TEXT PRIMARY KEY,
    name         TEXT NOT NULL,
    category     TEXT NOT NULL,
    region       TEXT NOT NULL,
    _batch_id    TEXT NOT NULL,
    _ingested_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS raw.transactions (
    transaction_id TEXT PRIMARY KEY,
    account_id     TEXT NOT NULL,
    merchant_id    TEXT NOT NULL,
    amount         NUMERIC(12, 2) NOT NULL,
    currency       TEXT NOT NULL,
    occurred_at    TIMESTAMPTZ NOT NULL,
    source         TEXT NOT NULL,
    ingested_at    TIMESTAMPTZ NOT NULL,
    _batch_id      TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_raw_transactions_batch ON raw.transactions (_batch_id);
