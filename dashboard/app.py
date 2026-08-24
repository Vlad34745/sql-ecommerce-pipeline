import os
import streamlit as st
import pandas as pd
import psycopg2

st.set_page_config(page_title="E-commerce Analytics", layout="wide")
st.title("E-commerce Analytics Dashboard")

url = os.getenv("DATABASE_URL")
if not url:
    st.error("DATABASE_URL is not configured.")
    st.stop()

def query(sql):
    with psycopg2.connect(url) as conn:
        return pd.read_sql_query(sql, conn)

kpi = query("""
SELECT COUNT(DISTINCT o.order_id) total_orders,
       COUNT(DISTINCT o.user_id) active_customers,
       ROUND(SUM(o.quantity*p.price),2) revenue,
       ROUND(SUM(o.quantity*p.price)/NULLIF(COUNT(DISTINCT o.order_id),0),2) aov
FROM orders o JOIN products p ON o.product_id=p.product_id
""").iloc[0]

c1,c2,c3,c4=st.columns(4)
c1.metric("Revenue", f"${kpi.revenue:,.2f}")
c2.metric("Orders", f"{int(kpi.total_orders):,}")
c3.metric("Customers", f"{int(kpi.active_customers):,}")
c4.metric("AOV", f"${kpi.aov:,.2f}")

st.subheader("Revenue by category")
category=query("""
SELECT p.category, SUM(o.quantity*p.price) revenue
FROM orders o JOIN products p ON o.product_id=p.product_id
GROUP BY p.category ORDER BY revenue DESC
""")
st.bar_chart(category.set_index("category"))

st.subheader("Top customers by LTV")
ltv=query("""
SELECT u.name, ROUND(SUM(o.quantity*p.price),2) lifetime_value
FROM users u JOIN orders o ON u.user_id=o.user_id
JOIN products p ON o.product_id=p.product_id
GROUP BY u.user_id,u.name
ORDER BY lifetime_value DESC LIMIT 10
""")
st.dataframe(ltv, use_container_width=True)
