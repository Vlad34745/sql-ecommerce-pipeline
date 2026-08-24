import pandas as pd
from core.postgres_manager import get_pg_connection

QUERIES = {
    "sales": """
        SELECT COUNT(DISTINCT o.order_id) AS total_orders,
               COUNT(DISTINCT o.user_id) AS active_customers,
               ROUND(SUM(o.quantity * p.price), 2) AS total_revenue,
               ROUND(SUM(o.quantity * p.price) / NULLIF(COUNT(DISTINCT o.order_id), 0), 2) AS average_order_value
        FROM orders o JOIN products p ON o.product_id = p.product_id;
    """,
    "ltv": """
        SELECT u.user_id, u.name, u.email,
               COUNT(o.order_id) AS total_orders,
               SUM(o.quantity) AS total_items_bought,
               ROUND(SUM(o.quantity * p.price), 2) AS lifetime_value_ltv,
               RANK() OVER (ORDER BY SUM(o.quantity * p.price) DESC) AS customer_rank
        FROM users u JOIN orders o ON u.user_id = o.user_id
        JOIN products p ON o.product_id = p.product_id
        GROUP BY u.user_id, u.name, u.email
        ORDER BY lifetime_value_ltv DESC LIMIT 10;
    """,
    "cohort": """
        WITH cohorts AS (
            SELECT user_id, DATE_TRUNC('month', registration_date)::date AS cohort_month FROM users
        ),
        activity AS (
            SELECT DISTINCT user_id, DATE_TRUNC('month', order_date)::date AS order_month FROM orders
        ),
        sizes AS (
            SELECT cohort_month, COUNT(*) AS cohort_size FROM cohorts GROUP BY cohort_month
        )
        SELECT c.cohort_month AS cohort,
               s.cohort_size,
               ((EXTRACT(YEAR FROM a.order_month) - EXTRACT(YEAR FROM c.cohort_month)) * 12
                + EXTRACT(MONTH FROM a.order_month) - EXTRACT(MONTH FROM c.cohort_month))::int AS month_number,
               COUNT(DISTINCT a.user_id) AS active_users,
               ROUND(COUNT(DISTINCT a.user_id)::numeric / s.cohort_size * 100, 2) AS retention_rate_pct
        FROM cohorts c JOIN activity a ON c.user_id=a.user_id
        JOIN sizes s ON c.cohort_month=s.cohort_month
        GROUP BY c.cohort_month, s.cohort_size, a.order_month
        ORDER BY c.cohort_month, month_number;
    """,
    "category": """
        SELECT p.category, SUM(o.quantity) AS units_sold,
               ROUND(SUM(o.quantity * p.price), 2) AS revenue
        FROM orders o JOIN products p ON o.product_id=p.product_id
        GROUP BY p.category ORDER BY revenue DESC;
    """
}

def run_query(name):
    with get_pg_connection() as conn:
        return pd.read_sql_query(QUERIES[name], conn)
