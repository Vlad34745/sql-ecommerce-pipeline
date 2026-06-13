-- 1. Загальні бізнес-метрики інтернет-магазину
SELECT 
    COUNT(DISTINCT o.order_id) as total_orders,
    COUNT(DISTINCT o.user_id) as active_customers,
    ROUND(SUM(o.quantity * p.price), 2) as total_revenue,
    ROUND(SUM(o.quantity * p.price) / COUNT(DISTINCT o.order_id), 2) as average_order_value (AOV)
FROM orders o
JOIN products p ON o.product_id = p.product_id;

-- 2. Аналіз категорій товарів за виручкою та обсягами продажів
SELECT 
    p.category,
    SUM(o.quantity) as total_units_sold,
    ROUND(SUM(o.quantity * p.price), 2) as category_revenue,
    ROUND((SUM(o.quantity * p.price) / (SELECT SUM(quantity * price) FROM orders JOIN products ON orders.product_id = products.product_id)) * 100, 2) as revenue_percentage
FROM orders o
JOIN products p ON o.product_id = p.product_id
GROUP BY p.category
ORDER BY category_revenue DESC;