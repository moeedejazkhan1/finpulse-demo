"""T033 - end-to-end smoke test against a *running* docker compose
stack (see quickstart.md). Every test skips cleanly if the stack isn't
up, rather than failing -- this file is meant to be run both in CI-like
conditions and ad hoc against a local `docker compose up -d`.
"""
import os
import sys
from pathlib import Path

import psycopg2
import pytest
import requests

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

PG_KWARGS = dict(
    host=os.environ.get("POSTGRES_HOST", "localhost"),
    port=os.environ.get("POSTGRES_PORT", "5432"),
    dbname=os.environ.get("POSTGRES_DB", "finpulse"),
    user=os.environ.get("POSTGRES_USER", "finpulse"),
    password=os.environ.get("POSTGRES_PASSWORD", "finpulse"),
)
METABASE_URL = os.environ.get("METABASE_URL", "http://localhost:3000")


def _pg_connection_or_skip():
    try:
        return psycopg2.connect(connect_timeout=3, **PG_KWARGS)
    except Exception as exc:  # noqa: BLE001
        pytest.skip(f"postgres not reachable ({exc}) -- is `docker compose up -d` running?")


def test_marts_transactions_populated():
    """SC-001: historical batch reaches the marts layer."""
    conn = _pg_connection_or_skip()
    try:
        with conn.cursor() as cur:
            cur.execute("select count(*) from marts.fct_transactions")
            (count,) = cur.fetchone()
        assert count > 0, "fct_transactions is empty -- has batch_load_dag run?"
    finally:
        conn.close()


def test_every_transaction_has_a_fraud_score():
    """SC-003: 100% of transactions get scored, none silently excluded."""
    conn = _pg_connection_or_skip()
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                select
                    (select count(*) from marts.fct_transactions) as txn_count,
                    (select count(*) from marts.fct_fraud_scores) as score_count
                """
            )
            txn_count, score_count = cur.fetchone()
        assert txn_count > 0, "no transactions to check -- run batch_load_dag first"
        assert score_count == txn_count, (
            f"{txn_count - score_count} transactions have no fraud score "
            "-- has fraud_scoring_dag run?"
        )
    finally:
        conn.close()


def test_metabase_dashboard_reachable():
    try:
        r = requests.get(f"{METABASE_URL}/api/health", timeout=3)
    except requests.RequestException as exc:
        pytest.skip(f"metabase not reachable ({exc})")
    assert r.status_code == 200
