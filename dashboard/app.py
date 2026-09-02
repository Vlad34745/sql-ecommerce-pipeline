import sys
from pathlib import Path

# Streamlit only adds this script's own folder (dashboard/) to sys.path,
# not the project root — so `core` wouldn't be importable without this,
# regardless of the working directory `streamlit run` is launched from.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import streamlit as st
import pandas as pd
import altair as alt
from core.postgres_manager import get_pg_engine

st.set_page_config(page_title="E-commerce Analytics", layout="wide")

# Hide Streamlit's default chrome (main menu, footer, deploy button) for a
# cleaner, more "product-like" look in portfolio screenshots.
st.markdown(
    """
    <style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    [data-testid="stAppDeployButton"] {display: none;}
    </style>
    """,
    unsafe_allow_html=True,
)

st.title("E-commerce Analytics Dashboard")

try:
    engine = get_pg_engine()
except ValueError as e:
    st.error(str(e))
    st.stop()


def query(sql, params=None):
    with engine.connect() as conn:
        return pd.read_sql_query(sql, conn, params=params)


# ---------------------------------------------------------------------------
# Filters
# ---------------------------------------------------------------------------
bounds = query("SELECT MIN(order_date) AS min_date, MAX(order_date) AS max_date FROM orders;").iloc[0]
categories = query("SELECT DISTINCT category FROM products ORDER BY category;")["category"].tolist()

with st.sidebar:
    st.header("Filters")
    date_range = st.date_input(
        "Order date range",
        value=(bounds.min_date, bounds.max_date),
        min_value=bounds.min_date,
        max_value=bounds.max_date,
    )
    selected_categories = st.multiselect("Category", options=categories, default=categories)

# date_input returns a single date until the user picks a second one — guard against that.
if isinstance(date_range, tuple) and len(date_range) == 2:
    start_date, end_date = date_range
else:
    start_date, end_date = bounds.min_date, bounds.max_date

if not selected_categories:
    st.warning("Select at least one category to see results.")
    st.stop()

filter_params = {"start": start_date, "end": end_date, "categories": tuple(selected_categories)}
category_filter_sql = "p.category IN %(categories)s"
date_filter_sql = "o.order_date BETWEEN %(start)s AND %(end)s"

# ---------------------------------------------------------------------------
# KPI row
# ---------------------------------------------------------------------------
kpi = query(
    f"""
    SELECT COUNT(DISTINCT o.order_id) total_orders,
           COUNT(DISTINCT o.user_id) active_customers,
           ROUND(SUM(o.quantity*p.price),2) revenue,
           ROUND(SUM(o.quantity*p.price)/NULLIF(COUNT(DISTINCT o.order_id),0),2) aov
    FROM orders o JOIN products p ON o.product_id=p.product_id
    WHERE {date_filter_sql} AND {category_filter_sql}
    """,
    filter_params,
).iloc[0]

c1, c2, c3, c4 = st.columns(4)
c1.metric("Revenue", f"${(kpi.revenue or 0):,.2f}")
c2.metric("Orders", f"{int(kpi.total_orders or 0):,}")
c3.metric("Customers", f"{int(kpi.active_customers or 0):,}")
c4.metric("AOV", f"${(kpi.aov or 0):,.2f}")

# ---------------------------------------------------------------------------
# Sales trend (revenue & orders by month)
# ---------------------------------------------------------------------------
st.subheader("Sales trend")
trend = query(
    f"""
    SELECT DATE_TRUNC('month', o.order_date)::date AS month,
           ROUND(SUM(o.quantity*p.price),2) AS revenue,
           COUNT(DISTINCT o.order_id) AS orders
    FROM orders o JOIN products p ON o.product_id=p.product_id
    WHERE {date_filter_sql} AND {category_filter_sql}
    GROUP BY month ORDER BY month
    """,
    filter_params,
)
tc1, tc2 = st.columns(2)
tc1.caption("Revenue by month")
tc1.line_chart(trend.set_index("month")["revenue"])
tc2.caption("Orders by month")
tc2.bar_chart(trend.set_index("month")["orders"])

# ---------------------------------------------------------------------------
# Revenue by category
# ---------------------------------------------------------------------------
st.subheader("Revenue by category")
category = query(
    f"""
    SELECT p.category, SUM(o.quantity*p.price) revenue
    FROM orders o JOIN products p ON o.product_id=p.product_id
    WHERE {date_filter_sql} AND {category_filter_sql}
    GROUP BY p.category ORDER BY revenue DESC
    """,
    filter_params,
)
st.bar_chart(category.set_index("category"))

# ---------------------------------------------------------------------------
# Top customers by LTV
# ---------------------------------------------------------------------------
st.subheader("Top customers by LTV")
ltv = query(
    f"""
    SELECT u.name AS customer,
           COUNT(o.order_id) AS orders,
           SUM(o.quantity) AS items,
           ROUND(SUM(o.quantity*p.price),2) AS ltv
    FROM users u JOIN orders o ON u.user_id=o.user_id
    JOIN products p ON o.product_id=p.product_id
    WHERE {date_filter_sql} AND {category_filter_sql}
    GROUP BY u.user_id, u.name
    ORDER BY ltv DESC LIMIT 10
    """,
    filter_params,
)
ltv.insert(0, "rank", range(1, len(ltv) + 1))
st.dataframe(ltv, width="stretch", hide_index=True)

# ---------------------------------------------------------------------------
# Cohort retention heatmap
# ---------------------------------------------------------------------------
# Retention is a full-history concept (a cohort is defined by registration
# month, not by the order-date filter above), so this section intentionally
# ignores the sidebar filters and always shows the complete picture.
st.subheader("Cohort retention")
cohort = query(
    """
    WITH cohorts AS (
        SELECT user_id, DATE_TRUNC('month', registration_date)::date AS cohort_month FROM users
    ),
    activity AS (
        SELECT DISTINCT user_id, DATE_TRUNC('month', order_date)::date AS order_month FROM orders
    ),
    sizes AS (
        SELECT cohort_month, COUNT(*) AS cohort_size FROM cohorts GROUP BY cohort_month
    )
    SELECT c.cohort_month::text AS cohort,
           ((EXTRACT(YEAR FROM a.order_month) - EXTRACT(YEAR FROM c.cohort_month)) * 12
            + EXTRACT(MONTH FROM a.order_month) - EXTRACT(MONTH FROM c.cohort_month))::int AS month_number,
           ROUND(COUNT(DISTINCT a.user_id)::numeric / s.cohort_size * 100, 2) AS retention_pct
    FROM cohorts c JOIN activity a ON c.user_id=a.user_id
    JOIN sizes s ON c.cohort_month=s.cohort_month
    GROUP BY c.cohort_month, s.cohort_size, a.order_month
    ORDER BY c.cohort_month, month_number;
    """
)

if cohort.empty:
    st.info("Not enough data yet to build a cohort retention view.")
else:
    heatmap = (
        alt.Chart(cohort)
        .mark_rect()
        .encode(
            x=alt.X("month_number:O", title="Months since first order"),
            y=alt.Y("cohort:O", title="Signup cohort", sort=None),
            color=alt.Color("retention_pct:Q", title="Retention %", scale=alt.Scale(scheme="blues")),
            tooltip=["cohort", "month_number", "retention_pct"],
        )
        .properties(height=28 * cohort["cohort"].nunique() + 40)
    )
    st.altair_chart(heatmap, width="stretch")