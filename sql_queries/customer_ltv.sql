-- Customer LTV and global rank
WITH customer_value AS (
    SELECT
        u.user_id,
        u.name,
        u.email,
        COUNT(o.order_id) AS total_orders,
        SUM(o.quantity) AS total_items_bought,
        SUM(o.quantity * p.price) AS lifetime_value_ltv
    FROM users u
    JOIN orders o ON u.user_id = o.user_id
    JOIN products p ON o.product_id = p.product_id
    GROUP BY u.user_id, u.name, u.email
)
SELECT *,
       RANK() OVER (ORDER BY lifetime_value_ltv DESC) AS customer_rank
FROM customer_value
ORDER BY lifetime_value_ltv DESC
LIMIT 10;
