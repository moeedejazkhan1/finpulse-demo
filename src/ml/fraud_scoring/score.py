"""Batch fraud-risk scoring (T020).

Reads marts.fct_transactions, scores every transaction with an
IsolationForest anomaly model, and writes risk_score + is_flagged to
marts.fct_fraud_scores. Run on a schedule by
airflow/dags/fraud_scoring_dag.py, after dbt has rebuilt the marts.

Constitution Check (see plan.md): this is an enrichment step, not a
dbt transformation -- dbt cannot run model inference, so scoring lives
here and writes its own marts table rather than editing fct_transactions.
"""
from __future__ import annotations

import datetime as dt
import sys
from pathlib import Path

import numpy as np
import psycopg2
import psycopg2.extras
from sklearn.ensemble import IsolationForest

sys.path.insert(0, str(Path(__file__).resolve().parent))
from features import build_features, load_transactions, pg_connect  # noqa: E402

FLAG_CONTAMINATION = 0.03  # top ~3% most anomalous scored as flagged


def ensure_table(cur) -> None:
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS marts.fct_fraud_scores (
            transaction_id TEXT PRIMARY KEY,
            risk_score     DOUBLE PRECISION NOT NULL,
            is_flagged     BOOLEAN NOT NULL,
            scored_at      TIMESTAMPTZ NOT NULL
        )
        """
    )


def score_transactions() -> tuple[int, int]:
    df = load_transactions()
    if df.empty:
        return 0, 0

    features, transaction_ids = build_features(df)

    model = IsolationForest(
        n_estimators=200,
        contamination=FLAG_CONTAMINATION,
        random_state=42,
    )
    model.fit(features)

    # decision_function: higher = more normal. Invert and min-max scale
    # to a 0-1 "risk" score so it reads naturally on a dashboard.
    raw_scores = -model.decision_function(features)
    risk_scores = (raw_scores - raw_scores.min()) / (raw_scores.max() - raw_scores.min() + 1e-9)
    is_flagged = model.predict(features) == -1  # -1 = anomaly per sklearn convention

    scored_at = dt.datetime.now(dt.timezone.utc)
    rows = [
        (tid, float(score), bool(flag), scored_at)
        for tid, score, flag in zip(transaction_ids, risk_scores, is_flagged)
    ]

    conn = pg_connect()
    try:
        with conn.cursor() as cur:
            ensure_table(cur)
            psycopg2.extras.execute_values(
                cur,
                """
                INSERT INTO marts.fct_fraud_scores (transaction_id, risk_score, is_flagged, scored_at)
                VALUES %s
                ON CONFLICT (transaction_id) DO UPDATE SET
                    risk_score = EXCLUDED.risk_score,
                    is_flagged = EXCLUDED.is_flagged,
                    scored_at  = EXCLUDED.scored_at
                """,
                rows,
            )
        conn.commit()
    finally:
        conn.close()

    return len(rows), int(np.sum(is_flagged))


if __name__ == "__main__":
    total, flagged = score_transactions()
    print(f"scored {total} transactions, {flagged} flagged as high risk")
