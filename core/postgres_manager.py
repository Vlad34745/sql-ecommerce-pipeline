import os

from dotenv import load_dotenv
from sqlalchemy import create_engine

from core.schema import POSTGRES_SCHEMA

load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL")


def get_pg_engine():
    """Create a SQLAlchemy engine for pandas analytics queries."""
    if not DATABASE_URL:
        raise ValueError("DATABASE_URL is not set. Copy .env.example to .env and configure it.")
    return create_engine(DATABASE_URL, pool_pre_ping=True)


def get_pg_connection():
    if not DATABASE_URL:
        raise ValueError("DATABASE_URL is not set. Copy .env.example to .env and configure it.")
    import psycopg2
    return psycopg2.connect(DATABASE_URL)


def init_postgres_db(reset: bool = False):
    """Create the PostgreSQL schema without deleting data unless reset=True."""
    with get_pg_connection() as conn:
        with conn.cursor() as cur:
            if reset:
                cur.execute("DROP TABLE IF EXISTS orders, products, users CASCADE;")
            cur.execute(POSTGRES_SCHEMA)
