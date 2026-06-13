import os
import psycopg2
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

def get_pg_connection():
    """Establishes a connection to the cloud PostgreSQL database."""
    if not DATABASE_URL:
        raise ValueError("[ERROR] DATABASE_URL not found in .env file!")
    return psycopg2.connect(DATABASE_URL)

def init_postgres_db():
    """Deploys the database schema in PostgreSQL (users, products, orders tables)."""
    print("[POSTGRES] Connecting to cloud database and initializing schema...")
    
    conn = get_pg_connection()
    cursor = conn.cursor()
    
    # 1. Users table (using SERIAL and DATE for PostgreSQL compliance)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        user_id SERIAL PRIMARY KEY,
        name VARCHAR(255) NOT NULL,
        email VARCHAR(255) UNIQUE NOT NULL,
        registration_date DATE NOT NULL
    );
    """)
    
    # 2. Products table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS products (
        product_id SERIAL PRIMARY KEY,
        product_name VARCHAR(255) NOT NULL,
        category VARCHAR(100) NOT NULL,
        price NUMERIC(10, 2) NOT NULL
    );
    """)
    
    # 3. Orders table with relational Foreign Keys
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS orders (
        order_id SERIAL PRIMARY KEY,
        user_id INTEGER REFERENCES users(user_id) ON DELETE CASCADE,
        product_id INTEGER REFERENCES products(product_id) ON DELETE RESTRICT,
        order_date TIMESTAMP NOT NULL,
        quantity INTEGER NOT NULL
    );
    """)
    
    # 4. Creating performance indexes for analytical query optimization
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_pg_orders_user ON orders(user_id);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_pg_orders_date ON orders(order_date);")
    
    conn.commit()
    cursor.close()
    conn.close()
    print("[POSTGRES] Database schema and indexes deployed to cloud successfully!")

if __name__ == "__main__":
    # Test execution to verify cloud database connection and schema setup
    init_postgres_db()