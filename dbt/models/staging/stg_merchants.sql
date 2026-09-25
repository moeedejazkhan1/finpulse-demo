select
    merchant_id,
    name as merchant_name,
    category,
    region,
    _batch_id
from {{ source('raw', 'merchants') }}
where merchant_id is not null
