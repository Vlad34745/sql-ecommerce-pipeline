import os
import sqlite3
from core.schema import SQLITE_SCHEMA

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "ecommerce_local.db")

def get_connection():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn

def init_db(reset: bool = False):
    with get_connection() as conn:
        if reset:
            conn.executescript("""
                DROP TABLE IF EXISTS orders;
                DROP TABLE IF EXISTS products;
                DROP TABLE IF EXISTS users;
            """)
        conn.executescript(SQLITE_SCHEMA)
