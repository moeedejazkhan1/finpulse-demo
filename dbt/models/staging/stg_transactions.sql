-- Deliberately source-agnostic: this model does not branch on `source`
-- (batch vs streaming). Per constitution Principle II (Unified
-- Transformation Path), one model serves both -- a future streaming
-- producer needs zero changes here to be modeled correctly.

with deduped as (
    select
        *,
        row_number() over (
            partition by transaction_id
            order by ingested_at desc
        ) as _rn
    from {{ source('raw', 'transactions') }}
)

select
    transaction_id,
    account_id,
    merchant_id,
    amount,
    currency,
    occurred_at,
    source,
    ingested_at,
    _batch_id
from deduped
where _rn = 1
  and amount > 0
