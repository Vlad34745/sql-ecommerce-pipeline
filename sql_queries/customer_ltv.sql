-- Розрахунок цінності клієнта (Lifetime Value) та ранжування за допомогою віконних функцій
SELECT 
    u.user_id,
    u.name,
    u.email,
    COUNT(o.order_id) as total_orders_placed,
    SUM(o.quantity) as total_items_bought,
    ROUND(SUM(o.quantity * p.price), 2) as lifetime_value_ltv,
    -- Приклад використання віконної функції для визначення рангу клієнта по виручці
    RANK() OVER (ORDER BY SUM(o.quantity * p.price) DESC) as customer_rank
FROM users u
JOIN orders o ON u.user_id = o.user_id
JOIN products p ON o.product_id = p.product_id
GROUP BY u.user_id, u.name, u.email
ORDER BY lifetime_value_ltv DESC
LIMIT 10;