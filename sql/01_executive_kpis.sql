-- Executive churn KPIs (SQLite / ANSI-friendly)
SELECT
    COUNT(*) AS customers,
    SUM(churn) AS churned_customers,
    ROUND(AVG(churn) * 100.0, 2) AS churn_rate_pct,
    ROUND(SUM(CASE WHEN churn = 0 THEN monthly_charges ELSE 0 END), 2) AS active_mrr,
    ROUND(SUM(CASE WHEN churn = 1 THEN annual_revenue ELSE 0 END), 2) AS annual_revenue_at_risk,
    ROUND(AVG(nps), 2) AS average_nps
FROM customer_churn;