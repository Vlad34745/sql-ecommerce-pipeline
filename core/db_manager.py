import sqlite3
import os

# Визначаємо шлях до бази даних (кладемо її в папку data)
DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "ecommerce_local.db")

def get_connection():
    """Створює та повертає підключення до бази даних SQLite з підтримкою Foreign Keys."""
    conn = sqlite3.connect(DB_PATH)
    # Обов'язково вмикаємо підтримку зовнішніх ключів (у SQLite вона вимкнена за замовчуванням)
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn

def init_db():
    """Створює схему бази даних: таблиці users, products, orders та індекси."""
    print(f"[DB] Initializing database at: {DB_PATH}")
    
    conn = get_connection()
    cursor = conn.cursor()
    
    # 1. Створюємо таблицю Користувачів (Users)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        user_id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        email TEXT UNIQUE NOT NULL,
        registration_date TEXT NOT NULL
    );
    """)
    
    # 2. Створюємо таблицю Товарів (Products)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS products (
        product_id INTEGER PRIMARY KEY AUTOINCREMENT,
        product_name TEXT NOT NULL,
        category TEXT NOT NULL,
        price REAL NOT NULL
    );
    """)
    
    # 3. Створюємо таблицю Замовлень (Orders)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS orders (
        order_id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        product_id INTEGER,
        order_date TEXT NOT NULL,
        quantity INTEGER NOT NULL,
        FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE,
        FOREIGN KEY (product_id) REFERENCES products(product_id) ON DELETE RESTRICT
    );
    """)
    
    # 4. Створюємо індекси для оптимізації майбутніх аналітичних SQL-запитів
    # Індекси пришвидшать операції JOIN та фільтрацію по датах у мільйони разів
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_orders_user ON orders(user_id);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_orders_date ON orders(order_date);")
    
    conn.commit()
    conn.close()
    print("[DB] Database schema and indexes deployed successfully!")

if __name__ == "__main__":
    # Тестовий запуск модуля напряму для перевірки
    init_db()