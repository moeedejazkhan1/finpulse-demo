-- Business-ready transaction fact. Supports the two US1 dashboard
-- KPIs (volume over time, revenue by merchant/region) directly via
-- date_trunc / group by on this one table.

select
    t.transaction_id,
    t.account_id,
    t.merchant_id,
    m.merchant_name,
    m.category as merchant_category,
    coalesce(m.region, a.region) as region,
    t.amount,
    t.currency,
    t.occurred_at,
    date_trunc('day', t.occurred_at) as occurred_date,
    t.source
from {{ ref('stg_transactions') }} t
left join {{ ref('dim_account') }} a on a.account_id = t.account_id
left join {{ ref('dim_merchant') }} m on m.merchant_id = t.merchant_id
