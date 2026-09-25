"""T022 - orchestrates: dbt run (pick up any new transactions) -> batch
fraud-risk scoring. Scheduled to run after batch_load_dag via a time
offset (both are @once for this demo; in a live system this would be
a data-aware/sensor trigger off batch_load_dag's completion).
"""
from __future__ import annotations

import datetime as dt

from airflow import DAG
from airflow.operators.bash import BashOperator

PROJECT_DIR = "/opt/airflow/project"

default_args = {
    "owner": "finpulse",
    "retries": 1,
    "retry_delay": dt.timedelta(minutes=2),
}

with DAG(
    dag_id="fraud_scoring_dag",
    description="Rebuild marts, then batch-score every transaction for fraud risk",
    default_args=default_args,
    schedule="@once",
    start_date=dt.datetime(2026, 1, 1),
    catchup=False,
    tags=["finpulse", "ml"],
) as dag:

    dbt_run = BashOperator(
        task_id="dbt_run_before_scoring",
        bash_command=f"cd {PROJECT_DIR}/dbt && dbt run --profiles-dir . --select marts",
    )

    score = BashOperator(
        task_id="score_fraud_risk",
        bash_command=f"cd {PROJECT_DIR}/src/ml/fraud_scoring && python score.py",
    )

    dbt_run >> score
