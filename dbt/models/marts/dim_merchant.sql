select
    merchant_id,
    merchant_name,
    category,
    region
from {{ ref('stg_merchants') }}
