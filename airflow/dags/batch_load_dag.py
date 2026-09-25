"""T015 - orchestrates: generate synthetic batch -> land in MinIO +
Postgres raw -> dbt run (staging + marts). Scheduled to run once
shortly after the stack comes up, satisfying spec.md SC-001.
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
    dag_id="batch_load_dag",
    description="Generate historical batch data, land it, and build staging+marts",
    default_args=default_args,
    schedule="@once",
    start_date=dt.datetime(2026, 1, 1),
    catchup=False,
    tags=["finpulse", "batch"],
) as dag:

    generate = BashOperator(
        task_id="generate_synthetic_data",
        bash_command=f"cd {PROJECT_DIR} && python src/datagen/generate.py --out data/batch",
    )

    load = BashOperator(
        task_id="load_to_minio_and_raw",
        bash_command=f"cd {PROJECT_DIR} && python src/datagen/load_batch.py --data-dir data/batch",
    )

    dbt_run = BashOperator(
        task_id="dbt_run_staging_and_marts",
        bash_command=f"cd {PROJECT_DIR}/dbt && dbt run --profiles-dir .",
    )

    generate >> load >> dbt_run
