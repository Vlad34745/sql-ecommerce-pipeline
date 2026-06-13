import random
import os
from datetime import datetime, timedelta
from faker import Faker
import pandas as pd

# Import both database managers
from core.db_manager import get_connection as get_sqlite_conn, init_db as init_sqlite_db
from core.postgres_manager import get_pg_connection, init_postgres_db

fake = Faker()

PRODUCT_TEMPLATES = [
    {"name": "Wireless Mouse", "category": "Electronics", "price": 25.0},
    {"name": "Mechanical Keyboard", "category": "Electronics", "price": 85.0},
    {"name": "Gaming Monitor 24'", "category": "Electronics", "price": 180.0},
    {"name": "Leather Office Chair", "category": "Furniture", "price": 220.0},
    {"name": "Standing Desk", "category": "Furniture", "price": 350.0},
    {"name": "Coffee Mug", "category": "Kitchen", "price": 12.5},
    {"name": "Stainless Steel Water Bottle", "category": "Kitchen", "price": 24.0},
    {"name": "Running Shoes", "category": "Apparel", "price": 95.0},
    {"name": "Cotton Hoodie", "category": "Apparel", "price": 45.0},
    {"name": "Yoga Mat", "category": "Sports", "price": 30.0}
]

def generate_raw_data(num_users=100, num_orders=800):
    """Generates clean, structured data in memory."""
    print(f"[ETL] Generating {num_users} users and {num_orders} orders in memory...")
    
    # 1. Products
    products = PRODUCT_TEMPLATES
    
    # 2. Users
    users = []
    start_date = datetime(2025, 1, 1)
    for _ in range(num_users):
        reg_date = start_date + timedelta(days=random.randint(0, 500))
        users.append({
            "name": fake.name(),
            "email": fake.unique.email(),
            "reg_date": reg_date
        })
        
    # 3. Orders
    orders = []
    for _ in range(num_orders):
        user_idx = random.randint(0, num_users - 1)
        prod_idx = random.randint(0, len(products) - 1)
        
        reg_date = users[user_idx]["reg_date"]
        days_after_reg = random.randint(0, 60)
        order_date = reg_date + timedelta(days=days_after_reg)
        
        if order_date > datetime.now():
            order_date = datetime.now()
            
        orders.append({
            "user_idx": user_idx,
            "product_idx": prod_idx,
            "order_date": order_date,
            "quantity": random.randint(1, 4)
        })
        
    return products, users, orders

def load_to_sqlite(products, users, orders):
    """Uploads generated data to local SQLite."""
    conn = get_sqlite_conn()
    cursor = conn.cursor()
    
    # Upload products
    prod_ids = []
    for p in products:
        cursor.execute("INSERT INTO products (product_name, category, price) VALUES (?, ?, ?);", (p["name"], p["category"], p["price"]))
        prod_ids.append(cursor.lastrowid)
        
    # Upload users
    user_ids = []
    for u in users:
        cursor.execute("INSERT INTO users (name, email, registration_date) VALUES (?, ?, ?);", (u["name"], u["email"], u["reg_date"].strftime("%Y-%m-%d")))
        user_ids.append(cursor.lastrowid)
        
    # Upload orders using executemany
    orders_batch = []
    for o in orders:
        orders_batch.append((user_ids[o["user_idx"]], prod_ids[o["product_idx"]], o["order_date"].strftime("%Y-%m-%d %H:%M:%S"), o["quantity"]))
        
    cursor.executemany("INSERT INTO orders (user_id, product_id, order_date, quantity) VALUES (?, ?, ?, ?);", orders_batch)
    conn.commit()
    conn.close()
    print("[SQLite] Local data sync completely successful!")

def load_to_postgres(products, users, orders):
    """Uploads generated data to cloud PostgreSQL."""
    print("[POSTGRES] Attempting to connect and sync to cloud...")
    conn = get_pg_connection()
    cursor = conn.cursor()
    
    # Upload products
    prod_ids = []
    for p in products:
        cursor.execute("INSERT INTO products (product_name, category, price) VALUES (%s, %s, %s) RETURNING product_id;", (p["name"], p["category"], p["price"]))
        prod_ids.append(cursor.fetchone()[0])
        
    # Upload users
    user_ids = []
    for u in users:
        cursor.execute("INSERT INTO users (name, email, registration_date) VALUES (%s, %s, %s) RETURNING user_id;", (u["name"], u["email"], u["reg_date"].date()))
        user_ids.append(cursor.fetchone()[0])
        
    # Upload orders
    orders_batch = []
    for o in orders:
        orders_batch.append((user_ids[o["user_idx"]], prod_ids[o["product_idx"]], o["order_date"], o["quantity"]))
        
    cursor.executemany("INSERT INTO orders (user_id, product_id, order_date, quantity) VALUES (%s, %s, %s, %s);", orders_batch)
    conn.commit()
    cursor.close()
    conn.close()
    print("[POSTGRES] Cloud Data sync completely successful!")

def run_postgres_analytics():
    """Calculates Cohort Retention Analysis in Cloud Postgres using PL/pgSQL."""
    conn = get_pg_connection()
    print("\n" + "="*50)
    print("   ☁️ CLOUD POSTGRES COHORT RETENTION REPORT      ")
    print("="*50)
    
    query_pg_cohort = """
    WITH user_cohorts AS (
        SELECT user_id, TO_CHAR(registration_date, 'YYYY-MM') as cohort_month FROM users
    ),
    user_orders AS (
        SELECT DISTINCT user_id, TO_CHAR(order_date, 'YYYY-MM') as order_month FROM orders
    ),
    cohort_diff AS (
        SELECT 
            c.cohort_month,
            c.user_id,
            (CAST(SUBSTRING(o.order_month FROM 1 FOR 4) AS INT) - CAST(SUBSTRING(c.cohort_month FROM 1 FOR 4) AS INT)) * 12 +
            (CAST(SUBSTRING(o.order_month FROM 6 FOR 2) AS INT) - CAST(SUBSTRING(c.cohort_month FROM 6 FOR 2) AS INT)) as month_num
        FROM user_cohorts c
        JOIN user_orders o ON c.user_id = o.user_id
    ),
    cohort_sizes AS (
        SELECT cohort_month, COUNT(DISTINCT user_id) as total_users FROM user_cohorts GROUP BY cohort_month
    )
    SELECT 
        d.cohort_month as cohort,
        s.total_users as size,
        d.month_num,
        ROUND((COUNT(DISTINCT d.user_id)::NUMERIC / s.total_users) * 100, 1) as retention_pct
    FROM cohort_diff d
    JOIN cohort_sizes s ON d.cohort_month = s.cohort_month
    WHERE d.month_num <= 3 AND d.month_num >= 0
    GROUP BY d.cohort_month, s.total_users, d.month_num
    ORDER BY d.cohort_month, d.month_num;
    """
    df_cohort = pd.read_sql_query(query_pg_cohort, conn)
    if not df_cohort.empty:
        df_pivot = df_cohort.pivot(index='cohort', columns='month_num', values='retention_pct')
        print(df_pivot.fillna(0).to_string())
    
    conn.close()

def run_pipeline():
    """Main execution method: runs synchronization across both fronts."""
    # 1. Reinitialize both databases (clear old data)
    init_sqlite_db()
    init_postgres_db()
    
    # 2. Generate data in memory (ensuring parity across databases)
    products, users, orders = generate_raw_data()
    
    # 3. Synchronous upload
    load_to_sqlite(products, users, orders)
    load_to_postgres(products, users, orders)
    
    # 4. Run cloud analytics
    run_postgres_analytics()

if __name__ == "__main__":
    run_pipeline()