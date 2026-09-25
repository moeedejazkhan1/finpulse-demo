select
    account_id,
    opened_at,
    region
from {{ ref('stg_accounts') }}
