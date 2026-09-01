from core.db_manager import get_connection, init_db
from core.generator import generate_raw_data
from core.loaders import load_to_sqlite


def test_sqlite_load_is_idempotent(tmp_path):
    import core.db_manager as db

    db.DB_PATH = str(tmp_path / "test.db")
    init_db(reset=True)
    data = generate_raw_data(10, 25, seed=11)

    load_to_sqlite(*data)
    load_to_sqlite(*data)

    with get_connection() as conn:
        users = conn.execute("SELECT COUNT(*) FROM users").fetchone()[0]
        products = conn.execute("SELECT COUNT(*) FROM products").fetchone()[0]
        orders = conn.execute("SELECT COUNT(*) FROM orders").fetchone()[0]
        duplicate_orders = conn.execute(
            "SELECT COUNT(*) - COUNT(DISTINCT source_order_id) FROM orders"
        ).fetchone()[0]

    assert users == 10
    assert products == 10
    assert orders == 25
    assert duplicate_orders == 0


def test_new_seed_appends_a_new_batch(tmp_path):
    import core.db_manager as db

    db.DB_PATH = str(tmp_path / "test.db")
    init_db(reset=True)

    load_to_sqlite(*generate_raw_data(10, 25, seed=11))
    load_to_sqlite(*generate_raw_data(10, 25, seed=12))

    with get_connection() as conn:
        users = conn.execute("SELECT COUNT(*) FROM users").fetchone()[0]
        orders = conn.execute("SELECT COUNT(*) FROM orders").fetchone()[0]

    assert users == 20
    assert orders == 50
