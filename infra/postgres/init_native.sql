-- Native (no-Docker) equivalent of init.sql. No separate `airflow`
-- database is needed here since orchestration is a plain script for
-- this environment (constitution v1.1.0 Deployment Environment Exception).

CREATE SCHEMA IF NOT EXISTS raw;
CREATE SCHEMA IF NOT EXISTS staging;
CREATE SCHEMA IF NOT EXISTS marts;

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
