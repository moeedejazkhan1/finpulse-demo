-- Cleaned/typed pass over raw.accounts. No business logic here
-- (medallion principle: staging = clean & type, marts = business-ready).

select
    account_id,
    opened_at,
    region,
    _batch_id
from {{ source('raw', 'accounts') }}
where account_id is not null
