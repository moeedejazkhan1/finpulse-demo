"""Synthetic account/merchant/transaction generation (T010, T011).

Produces the historical batch dataset: ~500 accounts, ~200 merchants,
~50,000 transactions, conforming to src.common.schema and
contracts/transaction-event-schema.md. Writes newline-delimited JSON
to a local directory that load_batch.py then lands in MinIO and Postgres.
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import random
import uuid
from decimal import Decimal
from pathlib import Path

from faker import Faker

import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from common.schema import (  # noqa: E402
    REGIONS,
    MERCHANT_CATEGORIES,
    Account,
    Merchant,
    Transaction,
    TransactionSource,
)

DEFAULT_N_ACCOUNTS = 500
DEFAULT_N_MERCHANTS = 200
DEFAULT_N_TRANSACTIONS = 50_000
HISTORY_DAYS = 180


def generate_accounts(n: int, faker: Faker) -> list[Account]:
    accounts = []
    for _ in range(n):
        opened_at = faker.date_time_between(
            start_date="-3y", end_date="-1d", tzinfo=dt.timezone.utc
        )
        accounts.append(
            Account(
                account_id=str(uuid.uuid4()),
                opened_at=opened_at,
                region=random.choice(REGIONS),
            )
        )
    return accounts


def generate_merchants(n: int, faker: Faker) -> list[Merchant]:
    merchants = []
    for _ in range(n):
        merchants.append(
            Merchant(
                merchant_id=str(uuid.uuid4()),
                name=faker.company(),
                category=random.choice(MERCHANT_CATEGORIES),
                region=random.choice(REGIONS),
            )
        )
    return merchants


def generate_transactions(
    n: int, accounts: list[Account], merchants: list[Merchant], faker: Faker
) -> list[Transaction]:
    now = dt.datetime.now(dt.timezone.utc)
    start = now - dt.timedelta(days=HISTORY_DAYS)
    transactions = []
    for _ in range(n):
        occurred_at = faker.date_time_between(
            start_date=start, end_date=now, tzinfo=dt.timezone.utc
        )
        amount = Decimal(str(round(random.uniform(2.5, 1800.0), 2)))
        transactions.append(
            Transaction(
                transaction_id=str(uuid.uuid4()),
                account_id=random.choice(accounts).account_id,
                merchant_id=random.choice(merchants).merchant_id,
                amount=amount,
                currency="USD",
                occurred_at=occurred_at,
                source=TransactionSource.BATCH,
                ingested_at=now,
            )
        )
    return transactions


def write_ndjson(records: list, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        for record in records:
            f.write(json.dumps(record.to_json_record()) + "\n")


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate FinPulse synthetic batch dataset")
    parser.add_argument("--out", default="data/batch", help="Output directory")
    parser.add_argument("--accounts", type=int, default=DEFAULT_N_ACCOUNTS)
    parser.add_argument("--merchants", type=int, default=DEFAULT_N_MERCHANTS)
    parser.add_argument("--transactions", type=int, default=DEFAULT_N_TRANSACTIONS)
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()

    random.seed(args.seed)
    faker = Faker()
    Faker.seed(args.seed)

    out_dir = Path(args.out)

    accounts = generate_accounts(args.accounts, faker)
    merchants = generate_merchants(args.merchants, faker)
    transactions = generate_transactions(args.transactions, accounts, merchants, faker)

    write_ndjson(accounts, out_dir / "accounts" / "accounts.ndjson")
    write_ndjson(merchants, out_dir / "merchants" / "merchants.ndjson")
    write_ndjson(transactions, out_dir / "transactions" / "transactions.ndjson")

    print(
        f"generated {len(accounts)} accounts, {len(merchants)} merchants, "
        f"{len(transactions)} transactions -> {out_dir}"
    )


if __name__ == "__main__":
    main()
