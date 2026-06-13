-- Cohort Analysis: Customer Retention Rate by Month
WITH user_cohorts AS (
    -- 1. Identify the registration month (cohort) for each user
    SELECT 
        user_id,
        strftime('%Y-%m', registration_date) as cohort_month
    FROM users
),
user_orders AS (
    -- 2. Identify the unique months in which each user placed an order
    SELECT DISTINCT
        user_id,
        strftime('%Y-%m', order_date) as order_month
    FROM orders
),
cohort_sizes AS (
    -- 3. Calculate the total number of unique users within each cohort
    SELECT 
        cohort_month,
        COUNT(DISTINCT user_id) as total_users
    FROM user_cohorts
    GROUP BY cohort_month
)
-- 4. Join components to calculate active users and retention percentages over time
SELECT 
    c.cohort_month as cohort,
    s.total_users as cohort_size,
    -- Calculate the number of months passed since the initial registration date
    (CAST(strftime('%Y', o.order_month) AS INT) - CAST(strftime('%Y', c.cohort_month) AS INT)) * 12 +
    (CAST(strftime('%m', o.order_month) AS INT) - CAST(strftime('%m', c.cohort_month) AS INT)) as month_number,
    COUNT(DISTINCT o.user_id) as active_users,
    ROUND(CAST(COUNT(DISTINCT o.user_id) AS REAL) / s.total_users * 100, 2) as retention_rate_pct
FROM user_cohorts c
JOIN user_orders o ON c.user_id = o.user_id
JOIN cohort_sizes s ON c.cohort_month = s.cohort_month
GROUP BY c.cohort_month, month_number
ORDER BY c.cohort_month, month_number;