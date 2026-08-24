-- PostgreSQL: core business KPIs
SELECT
    COUNT(DISTINCT o.order_id) AS total_orders,
    COUNT(DISTINCT o.user_id) AS active_customers,
    ROUND(SUM(o.quantity * p.price), 2) AS total_revenue,
    ROUND(SUM(o.quantity * p.price) / NULLIF(COUNT(DISTINCT o.order_id), 0), 2) AS average_order_value
FROM orders o
JOIN products p ON o.product_id = p.product_id;

-- Revenue and units by category
SELECT
    p.category,
    SUM(o.quantity) AS units_sold,
    ROUND(SUM(o.quantity * p.price), 2) AS category_revenue,
    ROUND(SUM(o.quantity * p.price) / SUM(SUM(o.quantity * p.price)) OVER () * 100, 2) AS revenue_percentage
FROM orders o
JOIN products p ON o.product_id = p.product_id
GROUP BY p.category
ORDER BY category_revenue DESC;
