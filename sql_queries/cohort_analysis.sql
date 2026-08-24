-- PostgreSQL cohort retention matrix
WITH cohorts AS (
    SELECT user_id, DATE_TRUNC('month', registration_date)::date AS cohort_month
    FROM users
),
activity AS (
    SELECT DISTINCT user_id, DATE_TRUNC('month', order_date)::date AS order_month
    FROM orders
),
sizes AS (
    SELECT cohort_month, COUNT(*) AS cohort_size
    FROM cohorts
    GROUP BY cohort_month
)
SELECT
    c.cohort_month AS cohort,
    s.cohort_size,
    ((EXTRACT(YEAR FROM a.order_month) - EXTRACT(YEAR FROM c.cohort_month)) * 12
     + EXTRACT(MONTH FROM a.order_month) - EXTRACT(MONTH FROM c.cohort_month))::int AS month_number,
    COUNT(DISTINCT a.user_id) AS active_users,
    ROUND(COUNT(DISTINCT a.user_id)::numeric / s.cohort_size * 100, 2) AS retention_rate_pct
FROM cohorts c
JOIN activity a ON c.user_id = a.user_id
JOIN sizes s ON c.cohort_month = s.cohort_month
GROUP BY c.cohort_month, s.cohort_size, a.order_month
ORDER BY c.cohort_month, month_number;
