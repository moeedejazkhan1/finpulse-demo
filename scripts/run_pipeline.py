"""Native, no-Docker orchestration substitute for Airflow.

Runs the exact same task graph as airflow/dags/batch_load_dag.py +
fraud_scoring_dag.py, sequentially, on demand:

  generate -> load to raw zone (S3-compatible) + Postgres raw -> dbt run
  (staging + marts) -> fraud scoring -> dbt run (pick up fct_fraud_scores)

See the constitution's "Deployment Environment Exception" (v1.1.0) for
why this exists instead of real Airflow on this machine.
"""
from __future__ import annotations

import os
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DBT_DIR = ROOT / "dbt"
PY = sys.executable
_bin_dir = Path(sys.executable).parent
DBT = str(_bin_dir / "dbt.exe") if (_bin_dir / "dbt.exe").exists() else "dbt"

# Native-run defaults -- points every component at the local processes
# started by scripts/native/*.ps1 / start-s3-mock.py instead of Docker
# service names.
NATIVE_ENV = {
    "POSTGRES_HOST": "localhost",
    "POSTGRES_PORT": "5432",
    "POSTGRES_DB": "finpulse",
    "POSTGRES_USER": "finpulse",
    "POSTGRES_PASSWORD": "finpulse",
    "MINIO_ENDPOINT": "http://localhost:9000",
    "MINIO_ROOT_USER": "finpulse",
    "MINIO_ROOT_PASSWORD": "finpulse123",
}


def run(step: str, cmd: list[str], cwd: Path, env: dict | None = None) -> None:
    print(f"\n=== {step} ===")
    print("  $ " + " ".join(cmd))
    full_env = os.environ.copy()
    full_env.update(NATIVE_ENV)
    if env:
        full_env.update(env)
    result = subprocess.run(cmd, cwd=cwd, env=full_env)
    if result.returncode != 0:
        print(f"!!! {step} failed with exit code {result.returncode}")
        sys.exit(result.returncode)
    print(f"--- {step} done ---")


def main() -> None:
    start = time.time()

    run(
        "Generate synthetic batch data",
        [PY, "src/datagen/generate.py", "--out", "data/batch"],
        cwd=ROOT,
    )

    run(
        "Land data in raw zone (S3-compatible) + Postgres raw",
        [PY, "src/datagen/load_batch.py", "--data-dir", "data/batch"],
        cwd=ROOT,
    )

    run(
        "dbt run (staging + marts)",
        [DBT, "run", "--profiles-dir", "."],
        cwd=DBT_DIR,
    )

    run(
        "Batch fraud-risk scoring",
        [PY, "score.py"],
        cwd=ROOT / "src" / "ml" / "fraud_scoring",
    )

    run(
        "dbt run again (marts unchanged, but re-asserts freshness)",
        [DBT, "run", "--profiles-dir", ".", "--select", "marts"],
        cwd=DBT_DIR,
    )

    elapsed = time.time() - start
    print(f"\nPipeline complete in {elapsed:.1f}s.")
    print("Every transaction in marts.fct_transactions should now have a matching row")
    print("in marts.fct_fraud_scores. Open Metabase to see the dashboard.")


if __name__ == "__main__":
    main()
