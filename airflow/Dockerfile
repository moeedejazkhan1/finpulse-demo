# Extends the official Airflow image with the project's Python deps
# (dbt-postgres, faker, scikit-learn, ...) so DAGs can shell out to
# src/datagen and src/ml/fraud_scoring, and run `dbt run` directly.
FROM apache/airflow:2.9.3-python3.11

COPY requirements.txt /requirements.txt
RUN pip install --no-cache-dir -r /requirements.txt
