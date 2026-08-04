-- Retention proxy by signup cohort.
WITH cohorts AS (
    SELECT
        SUBSTR(signup_date, 1, 7) AS signup_month,
        COUNT(*) AS customers,
        SUM(CASE WHEN churn = 0 THEN 1 ELSE 0 END) AS retained_customers,
        AVG(tenure_months) AS avg_tenure_months
    FROM customer_churn
    GROUP BY SUBSTR(signup_date, 1, 7)
)
SELECT
    signup_month,
    customers,
    retained_customers,
    ROUND(retained_customers * 100.0 / customers, 2) AS retention_rate_pct,
    ROUND(avg_tenure_months, 1) AS avg_tenure_months
FROM cohorts
ORDER BY signup_month;