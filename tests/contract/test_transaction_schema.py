"""T031 (scoped to the batch path -- no streaming producer exists yet).

Validates that src/datagen's output conforms to the shared contract in
contracts/transaction-event-schema.md, via the same validator any
future streaming producer's output would also be checked against.
"""
import datetime as dt
import random
import uuid
from decimal import Decimal

from faker import Faker

from common.schema import (
    Account,
    Merchant,
    SchemaValidationError,
    Transaction,
    TransactionSource,
    validate_transaction_record,
)
from datagen.generate import generate_accounts, generate_merchants, generate_transactions


def test_generated_accounts_conform_to_schema():
    faker = Faker()
    Faker.seed(1)
    accounts = generate_accounts(10, faker)
    assert len(accounts) == 10
    for a in accounts:
        assert isinstance(a, Account)


def test_generated_transactions_conform_to_schema():
    faker = Faker()
    Faker.seed(1)
    accounts = generate_accounts(5, faker)
    merchants = generate_merchants(5, faker)
    transactions = generate_transactions(20, accounts, merchants, faker)

    assert len(transactions) == 20
    for txn in transactions:
        record = txn.to_json_record()
        # Round-trips through the same validator a streaming consumer
        # would use -- this IS the contract test, not a description of it.
        revalidated = validate_transaction_record(record)
        assert revalidated.transaction_id == txn.transaction_id
        assert revalidated.source == TransactionSource.BATCH


def test_batch_and_a_hypothetical_streaming_record_share_one_shape():
    """The contract's whole point: source must be a pass-through
    attribute, never a switch that changes the record shape."""
    now = dt.datetime.now(dt.timezone.utc)
    batch_record = Transaction(
        transaction_id=str(uuid.uuid4()),
        account_id=str(uuid.uuid4()),
        merchant_id=str(uuid.uuid4()),
        amount=Decimal("10.00"),
        currency="USD",
        occurred_at=now,
        source=TransactionSource.BATCH,
        ingested_at=now,
    ).to_json_record()

    streaming_record = dict(batch_record)
    streaming_record["source"] = "streaming"
    streaming_record["transaction_id"] = str(uuid.uuid4())

    assert set(batch_record.keys()) == set(streaming_record.keys())
    validate_transaction_record(batch_record)
    validate_transaction_record(streaming_record)


def test_negative_amount_is_rejected():
    now = dt.datetime.now(dt.timezone.utc)
    try:
        Transaction(
            transaction_id=str(uuid.uuid4()),
            account_id=str(uuid.uuid4()),
            merchant_id=str(uuid.uuid4()),
            amount=Decimal("-5.00"),
            currency="USD",
            occurred_at=now,
            source=TransactionSource.BATCH,
            ingested_at=now,
        )
        assert False, "expected SchemaValidationError"
    except SchemaValidationError:
        pass
