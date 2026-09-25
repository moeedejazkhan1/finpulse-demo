"""Feature extraction (T019) for fraud-risk scoring.

Reads dbt's fct_transactions marts table and derives per-transaction
features. No labels exist (synthetic data has no ground-truth fraud),
which is why score.py uses an unsupervised model -- see research.md.
"""
from __future__ import annotations

import os

import pandas as pd
import psycopg2


def pg_connect():
    return psycopg2.connect(
        host=os.environ.get("POSTGRES_HOST", "localhost"),
        port=os.environ.get("POSTGRES_PORT", "5432"),
        dbname=os.environ.get("POSTGRES_DB", "finpulse"),
        user=os.environ.get("POSTGRES_USER", "finpulse"),
        password=os.environ.get("POSTGRES_PASSWORD", "finpulse"),
    )


def load_transactions() -> pd.DataFrame:
    conn = pg_connect()
    try:
        df = pd.read_sql(
            """
            select transaction_id, account_id, merchant_category, amount, occurred_at
            from marts.fct_transactions
            """,
            conn,
        )
    finally:
        conn.close()
    return df


def build_features(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df["occurred_at"] = pd.to_datetime(df["occurred_at"])
    df["hour_of_day"] = df["occurred_at"].dt.hour
    df["amount"] = df["amount"].astype(float)

    # Account velocity: how many transactions this account has made overall.
    # A crude but demo-legible anomaly signal -- accounts transacting far
    # more often than typical are more "anomalous" to the model.
    velocity = df.groupby("account_id")["transaction_id"].transform("count")
    df["account_velocity"] = velocity

    category_dummies = pd.get_dummies(df["merchant_category"], prefix="cat")

    feature_cols = pd.concat(
        [df[["amount", "hour_of_day", "account_velocity"]], category_dummies],
        axis=1,
    )
    return feature_cols.fillna(0), df["transaction_id"]
