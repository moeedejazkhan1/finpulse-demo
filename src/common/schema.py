"""Shared Account/Merchant/Transaction schema.

This is the contract referenced by
specs/001-transaction-analytics/contracts/transaction-event-schema.md.
The batch loader (src/datagen) is the only current producer, but any
future streaming producer MUST emit records validated by these same
classes -- that is what "unified transformation path" means in practice.
"""
from __future__ import annotations

import datetime as _dt
from dataclasses import dataclass, field, asdict
from decimal import Decimal
from enum import Enum
from typing import Any


REGIONS = ("US-East", "US-West", "EU", "APAC")
MERCHANT_CATEGORIES = ("grocery", "travel", "electronics", "dining", "utilities", "retail")


class TransactionSource(str, Enum):
    BATCH = "batch"
    STREAMING = "streaming"


class SchemaValidationError(ValueError):
    pass


@dataclass(frozen=True)
class Account:
    account_id: str
    opened_at: _dt.datetime
    region: str

    def __post_init__(self) -> None:
        if self.region not in REGIONS:
            raise SchemaValidationError(f"invalid region: {self.region!r}")

    def to_json_record(self) -> dict[str, Any]:
        return {
            "account_id": self.account_id,
            "opened_at": self.opened_at.isoformat(),
            "region": self.region,
        }


@dataclass(frozen=True)
class Merchant:
    merchant_id: str
    name: str
    category: str
    region: str

    def __post_init__(self) -> None:
        if self.category not in MERCHANT_CATEGORIES:
            raise SchemaValidationError(f"invalid category: {self.category!r}")
        if self.region not in REGIONS:
            raise SchemaValidationError(f"invalid region: {self.region!r}")

    def to_json_record(self) -> dict[str, Any]:
        return {
            "merchant_id": self.merchant_id,
            "name": self.name,
            "category": self.category,
            "region": self.region,
        }


@dataclass(frozen=True)
class Transaction:
    transaction_id: str
    account_id: str
    merchant_id: str
    amount: Decimal
    currency: str
    occurred_at: _dt.datetime
    source: TransactionSource
    ingested_at: _dt.datetime = field(default_factory=lambda: _dt.datetime.now(_dt.timezone.utc))

    def __post_init__(self) -> None:
        if self.amount <= 0:
            raise SchemaValidationError(f"amount must be > 0, got {self.amount}")
        if self.currency != "USD":
            raise SchemaValidationError(f"unsupported currency: {self.currency!r}")
        if self.occurred_at > self.ingested_at:
            raise SchemaValidationError("occurred_at must be <= ingested_at")

    def to_json_record(self) -> dict[str, Any]:
        return {
            "transaction_id": self.transaction_id,
            "account_id": self.account_id,
            "merchant_id": self.merchant_id,
            "amount": str(self.amount),
            "currency": self.currency,
            "occurred_at": self.occurred_at.isoformat(),
            "source": self.source.value,
            "ingested_at": self.ingested_at.isoformat(),
        }


def validate_transaction_record(record: dict[str, Any]) -> Transaction:
    """Parse+validate a raw JSON record against the shared contract.

    Used by tests/contract/test_transaction_schema.py to confirm any
    producer's output conforms, regardless of which producer wrote it.
    """
    try:
        return Transaction(
            transaction_id=record["transaction_id"],
            account_id=record["account_id"],
            merchant_id=record["merchant_id"],
            amount=Decimal(str(record["amount"])),
            currency=record["currency"],
            occurred_at=_dt.datetime.fromisoformat(record["occurred_at"]),
            source=TransactionSource(record["source"]),
            ingested_at=_dt.datetime.fromisoformat(record["ingested_at"]),
        )
    except (KeyError, ValueError) as exc:
        raise SchemaValidationError(f"malformed transaction record: {exc}") from exc
