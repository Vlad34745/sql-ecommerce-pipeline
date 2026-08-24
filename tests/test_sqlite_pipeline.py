import sqlite3
from core.db_manager import init_db, get_connection
from core.generator import generate_raw_data
from core.loaders import load_to_sqlite

def test_sqlite_load_is_idempotent(tmp_path, monkeypatch):
    import core.db_manager as db
    db.DB_PATH = str(tmp_path / "test.db")
    init_db(reset=True)
    data = generate_raw_data(10, 25, seed=11)
    load_to_sqlite(*data)
    load_to_sqlite(*data)

    with get_connection() as conn:
        users = conn.execute("SELECT COUNT(*) FROM users").fetchone()[0]
        orders = conn.execute("SELECT COUNT(*) FROM orders").fetchone()[0]
    assert users == 10
    assert orders == 25
