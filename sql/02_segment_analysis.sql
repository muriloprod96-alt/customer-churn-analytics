-- Rank segments by churn and revenue exposure.
WITH segment_metrics AS (
    SELECT
        region,
        plan,
        contract,
        COUNT(*) AS customers,
        SUM(churn) AS churned_customers,
        AVG(churn) AS churn_rate,
        SUM(CASE WHEN churn = 1 THEN annual_revenue ELSE 0 END) AS revenue_at_risk
    FROM customer_churn
    GROUP BY region, plan, contract
)
SELECT
    *,
    ROUND(churn_rate * 100.0, 2) AS churn_rate_pct,
    DENSE_RANK() OVER (ORDER BY churn_rate DESC) AS churn_rank
FROM segment_metrics
WHERE customers >= 20
ORDER BY churn_rate DESC, revenue_at_risk DESC;