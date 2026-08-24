import os
from dotenv import load_dotenv
from core.schema import POSTGRES_SCHEMA

load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL")

def get_pg_connection():
    if not DATABASE_URL:
        raise ValueError("DATABASE_URL is not set. Copy .env.example to .env and configure it.")
    import psycopg2
    return psycopg2.connect(DATABASE_URL)

def init_postgres_db(reset: bool = False):
    with get_pg_connection() as conn:
        with conn.cursor() as cur:
            if reset:
                cur.execute("DROP TABLE IF EXISTS orders, products, users CASCADE;")
            cur.execute(POSTGRES_SCHEMA)
