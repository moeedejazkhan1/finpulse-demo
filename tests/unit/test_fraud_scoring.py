"""T032 - unit tests for the feature-extraction logic in
src/ml/fraud_scoring/features.py. Does not require a live Postgres;
build_features operates on an in-memory DataFrame.
"""
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src" / "ml" / "fraud_scoring"))
from features import build_features  # noqa: E402


def _sample_df() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "transaction_id": "t1",
                "account_id": "a1",
                "merchant_category": "grocery",
                "amount": 12.50,
                "occurred_at": "2026-09-01T10:00:00+00:00",
            },
            {
                "transaction_id": "t2",
                "account_id": "a1",
                "merchant_category": "travel",
                "amount": 899.00,
                "occurred_at": "2026-09-01T23:00:00+00:00",
            },
            {
                "transaction_id": "t3",
                "account_id": "a2",
                "merchant_category": "grocery",
                "amount": 40.00,
                "occurred_at": "2026-09-02T09:00:00+00:00",
            },
        ]
    )


def test_build_features_shape_matches_input_rows():
    features, transaction_ids = build_features(_sample_df())
    assert len(features) == 3
    assert list(transaction_ids) == ["t1", "t2", "t3"]


def test_hour_of_day_extracted_correctly():
    features, _ = build_features(_sample_df())
    assert features.loc[0, "hour_of_day"] == 10
    assert features.loc[1, "hour_of_day"] == 23


def test_account_velocity_counts_per_account():
    features, _ = build_features(_sample_df())
    # account a1 has 2 transactions, a2 has 1
    assert features.loc[0, "account_velocity"] == 2
    assert features.loc[1, "account_velocity"] == 2
    assert features.loc[2, "account_velocity"] == 1


def test_merchant_category_one_hot_encoded():
    features, _ = build_features(_sample_df())
    assert "cat_grocery" in features.columns
    assert "cat_travel" in features.columns
    assert features.loc[0, "cat_grocery"] == 1
    assert features.loc[0, "cat_travel"] == 0
