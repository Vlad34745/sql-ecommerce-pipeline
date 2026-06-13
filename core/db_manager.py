import sqlite3
import os

# Define the database path (stored inside the 'data' directory)
DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "ecommerce_local.db")

def get_connection():
    """Establishes and returns a connection to the SQLite database with Foreign Keys enabled."""
    conn = sqlite3.connect(DB_PATH)
    # Explicitly enable Foreign Key support (disabled by default in SQLite)
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn

def init_db():
    """Deploys the database schema: initializes users, products, orders tables, and indexes."""
    print(f"[DB] Initializing database at: {DB_PATH}")
    
    conn = get_connection()
    cursor = conn.cursor()
    
    # 1. Create the Users table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        user_id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        email TEXT UNIQUE NOT NULL,
        registration_date TEXT NOT NULL
    );
    """)
    
    # 2. Create the Products table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS products (
        product_id INTEGER PRIMARY KEY AUTOINCREMENT,
        product_name TEXT NOT NULL,
        category TEXT NOT NULL,
        price REAL NOT NULL
    );
    """)
    
    # 3. Create the Orders table with Foreign Key constraints
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
    
    # 4. Create database indexes to optimize future analytical SQL queries
    # Indexes drastically speed up JOIN operations and date filtering under heavy loads
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_orders_user ON orders(user_id);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_orders_date ON orders(order_date);")
    
    conn.commit()
    conn.close()
    print("[DB] Database schema and indexes deployed successfully!")

if __name__ == "__main__":
    # Test execution to verify database creation and schema validation
    init_db()