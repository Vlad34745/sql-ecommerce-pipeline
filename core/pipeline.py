import random
from datetime import datetime, timedelta
from faker import Faker
import pandas as pd
from core.db_manager import get_connection, init_db

fake = Faker()

# Фіксований набір товарів для наочності аналітики
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

def generate_and_load_data(num_users=100, num_orders=800):
    """Генерує фейкові дані інтернет-магазину та завантажує їх в SQLite."""
    conn = get_connection()
    cursor = conn.cursor()
    
    print(f"[ETL] Generating {num_users} users and {num_orders} orders...")
    
    # 1. Завантаження Товарів (Products)
    products_data = []
    for p in PRODUCT_TEMPLATES:
        cursor.execute(
            "INSERT INTO products (product_name, category, price) VALUES (?, ?, ?);",
            (p["name"], p["category"], p["price"])
        )
        products_data.append(cursor.lastrowid) # Зберігаємо згенеровані ID товарів
        
    # 2. Генеруємо та завантажуємо Користувачів (Users)
    user_ids = []
    start_date = datetime(2025, 1, 1) # Історія за останні 1.5 роки
    
    for _ in range(num_users):
        name = fake.name()
        email = fake.unique.email()
        # Дата реєстрації випадкова протягом 2025-2026 років
        reg_date = start_date + timedelta(days=random.randint(0, 500))
        reg_date_str = reg_date.strftime("%Y-%m-%d")
        
        cursor.execute(
            "INSERT INTO users (name, email, registration_date) VALUES (?, ?, ?);",
            (name, email, reg_date_str)
        )
        user_ids.append((cursor.lastrowid, reg_date))

    # 3. Генеруємо та завантажуємо Замовлення (Orders)
    # Використовуємо транзакцію для мега-швидкого завантаження
    orders_batch = []
    for _ in range(num_orders):
        # Обираємо випадкового користувача
        user_id, reg_date = random.choice(user_ids)
        product_id = random.choice(products_data)
        
        # Дата замовлення має бути ПІСЛЯ дати реєстрації користувача
        days_after_reg = random.randint(0, 60)
        order_date = reg_date + timedelta(days=days_after_reg)
        # Обмежуємо поточною датою (червень 2026)
        if order_date > datetime.now():
            order_date = datetime.now()
            
        order_date_str = order_date.strftime("%Y-%m-%d %H:%M:%S")
        quantity = random.randint(1, 4)
        
        orders_batch.append((user_id, product_id, order_date_str, quantity))
        
    cursor.executemany(
        "INSERT INTO orders (user_id, product_id, order_date, quantity) VALUES (?, ?, ?, ?);",
        orders_batch
    )
    
    conn.commit()
    conn.close()
    print("[ETL] Data generation and loading complete successfully!")

def run_analytics():
    """Зчитує SQL-файли та виводить аналітичні звіти в консоль через Pandas."""
    conn = get_connection()
    
    print("\n" + "="*50)
    print("      🛒 BUSINESS INTELLIGENCE REPORT (SQL)     ")
    print("="*50)
    
    # 1. Звіт по категоріях
    print("\n[📊] TOP CATEGORIES BY REVENUE:")
    query_categories = """
    SELECT p.category, SUM(o.quantity) as units_sold, ROUND(SUM(o.quantity * p.price), 2) as revenue
    FROM orders o JOIN products p ON o.product_id = p.product_id
    GROUP BY p.category ORDER BY revenue DESC;
    """
    df_cat = pd.read_sql_query(query_categories, conn)
    print(df_cat.to_string(index=False))
    
    # 2. Звіт по Customer LTV
    print("\n[💎] TOP 5 VALUABLE CUSTOMERS (LTV):")
    query_ltv = """
    SELECT u.name, COUNT(o.order_id) as orders_count, ROUND(SUM(o.quantity * p.price), 2) as ltv
    FROM users u 
    JOIN orders o ON u.user_id = o.user_id
    JOIN products p ON o.product_id = p.product_id
    GROUP BY u.user_id ORDER BY ltv DESC LIMIT 5;
    """
    df_ltv = pd.read_sql_query(query_ltv, conn)
    print(df_ltv.to_string(index=False))
    
    # 3. Новий звіт: Когортний аналіз (Retention)
    print("\n[📊] COHORT RETENTION RATE ANALYSIS (First 3 Months):")
    query_cohort = """
    WITH user_cohorts AS (
        SELECT user_id, 
               strftime('%Y-%m', registration_date) as cohort_month
        FROM users
    ),
    user_orders AS (
        SELECT DISTINCT user_id, 
               strftime('%Y-%m', order_date) as order_month
        FROM orders
    ),
    cohort_diff AS (
        SELECT 
            c.cohort_month,
            c.user_id,
            -- Рахуємо різницю в місяцях напряму через конвертацію в числа
            (CAST(SUBSTR(o.order_month, 1, 4) AS INT) - CAST(SUBSTR(c.cohort_month, 1, 4) AS INT)) * 12 +
            (CAST(SUBSTR(o.order_month, 6, 2) AS INT) - CAST(SUBSTR(c.cohort_month, 6, 2) AS INT)) as month_num
        FROM user_cohorts c
        JOIN user_orders o ON c.user_id = o.user_id
    ),
    cohort_sizes AS (
        SELECT cohort_month, COUNT(DISTINCT user_id) as total_users 
        FROM user_cohorts 
        GROUP BY cohort_month
    )
    SELECT 
        d.cohort_month as cohort,
        s.total_users as size,
        d.month_num,
        ROUND(CAST(COUNT(DISTINCT d.user_id) AS REAL) / s.total_users * 100, 1) as retention_pct
    FROM cohort_diff d
    JOIN cohort_sizes s ON d.cohort_month = s.cohort_month
    WHERE d.month_num <= 3 AND d.month_num >= 0
    GROUP BY d.cohort_month, d.month_num
    ORDER BY d.cohort_month, d.month_num;
    """
    df_cohort = pd.read_sql_query(query_cohort, conn)
    
    if not df_cohort.empty:
        df_pivot = df_cohort.pivot(index='cohort', columns='month_num', values='retention_pct')
        print(df_pivot.fillna(0).to_string())
    else:
        print("No cohort data found. Check date formats.")
    
    # ТЕПЕР З'ЄДНАННЯ ЗАКРИВАЄТЬСЯ СУВОРО В КІНЦІ ВСІХ ЗАПИТІВ
    conn.close()

def run_pipeline():
    """Повний запуск: скидання бази, генерація та виведення аналітики."""
    init_db()
    generate_and_load_data()
    run_analytics() # Додаємо автоматичний виклик аналітики

if __name__ == "__main__":
    run_pipeline()