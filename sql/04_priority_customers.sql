-- Action list: active customers with the highest retention priority.
SELECT
    customer_id,
    region,
    plan,
    contract,
    monthly_charges,
    nps,
    support_tickets,
    late_payments,
    last_login_days,
    risk_score,
    annual_revenue
FROM customer_churn
WHERE churn = 0
  AND risk_segment = 'Alto'
ORDER BY risk_score DESC, annual_revenue DESC
LIMIT 100;