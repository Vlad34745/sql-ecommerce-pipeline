-- Когортний аналіз: утримання клієнтів (Retention Rate) по місяцях
WITH user_cohorts AS (
    -- 1. Визначаємо місяць реєстрації (когорту) для кожного користувача
    SELECT 
        user_id,
        strftime('%Y-%m', registration_date) as cohort_month
    FROM users
),
user_orders AS (
    -- 2. Визначаємо місяці, в яких кожен користувач робив замовлення
    SELECT DISTINCT
        user_id,
        strftime('%Y-%m', order_date) as order_month
    FROM orders
),
cohort_sizes AS (
    -- 3. Рахуємо загальну кількість користувачів у кожній когорті
    SELECT 
        cohort_month,
        COUNT(DISTINCT user_id) as total_users
    FROM user_cohorts
    GROUP BY cohort_month
)
-- 4. Об'єднуємо все разом, щоб порахувати кількість активних користувачів по місяцях
SELECT 
    c.cohort_month,
    s.total_users as cohort_size,
    -- Рахуємо кількість місяців, що минули з моменту реєстрації
    (CAST(strftime('%Y', o.order_month) AS INT) - CAST(strftime('%Y', c.cohort_month) AS INT)) * 12 +
    (CAST(strftime('%m', o.order_month) AS INT) - CAST(strftime('%m', c.cohort_month) AS INT)) as month_number,
    COUNT(DISTINCT o.user_id) as active_users,
    ROUND(CAST(COUNT(DISTINCT o.user_id) AS REAL) / s.total_users * 100, 2) as retention_rate_pct
FROM user_cohorts c
JOIN user_orders o ON c.user_id = o.user_id
JOIN cohort_sizes s ON c.cohort_month = s.cohort_month
GROUP BY c.cohort_month, month_number
ORDER BY c.cohort_month, month_number;