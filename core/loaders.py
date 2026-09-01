from core.db_manager import get_connection
from core.postgres_manager import get_pg_connection


def load_to_sqlite(products, users, orders):
    """Idempotently load a generated batch into SQLite."""
    with get_connection() as conn:
        conn.executemany(
            """INSERT INTO products(source_product_id, product_name, category, price)
               VALUES (?, ?, ?, ?)
               ON CONFLICT(source_product_id) DO UPDATE SET
                 product_name=excluded.product_name,
                 category=excluded.category,
                 price=excluded.price""",
            [(p["source_product_id"], p["name"], p["category"], p["price"]) for p in products],
        )

        conn.executemany(
            """INSERT INTO users(source_user_id, name, email, registration_date)
               VALUES (?, ?, ?, ?)
               ON CONFLICT(source_user_id) DO UPDATE SET
                 name=excluded.name,
                 email=excluded.email,
                 registration_date=excluded.registration_date""",
            [(u["source_user_id"], u["name"], u["email"], u["reg_date"].isoformat()) for u in users],
        )

        order_rows = [
            (
                o["source_order_id"],
                o["source_user_id"],
                o["source_product_id"],
                o["order_date"].isoformat(sep=" "),
                o["quantity"],
                o["source_product_id"],
                o["source_user_id"],
            )
            for o in orders
        ]
        conn.executemany(
            """INSERT INTO orders(
                    source_order_id, source_user_id, source_product_id,
                    user_id, product_id, order_date, quantity
               )
               SELECT ?, ?, ?, u.user_id, p.product_id, ?, ?
               FROM users u
               JOIN products p
                 ON p.source_product_id = ?
               WHERE u.source_user_id = ?
               ON CONFLICT(source_order_id) DO UPDATE SET
                 source_user_id=excluded.source_user_id,
                 source_product_id=excluded.source_product_id,
                 order_date=excluded.order_date,
                 quantity=excluded.quantity,
                 user_id=excluded.user_id,
                 product_id=excluded.product_id""",
            order_rows,
        )


def load_to_postgres(products, users, orders):
    """Idempotently load a generated batch into PostgreSQL."""
    with get_pg_connection() as conn:
        with conn.cursor() as cur:
            cur.executemany(
                """INSERT INTO products(source_product_id, product_name, category, price)
                   VALUES (%s, %s, %s, %s)
                   ON CONFLICT(source_product_id) DO UPDATE SET
                     product_name=EXCLUDED.product_name,
                     category=EXCLUDED.category,
                     price=EXCLUDED.price""",
                [(p["source_product_id"], p["name"], p["category"], p["price"]) for p in products],
            )

            cur.executemany(
                """INSERT INTO users(source_user_id, name, email, registration_date)
                   VALUES (%s, %s, %s, %s)
                   ON CONFLICT(source_user_id) DO UPDATE SET
                     name=EXCLUDED.name,
                     email=EXCLUDED.email,
                     registration_date=EXCLUDED.registration_date""",
                [(u["source_user_id"], u["name"], u["email"], u["reg_date"]) for u in users],
            )

            cur.executemany(
                """INSERT INTO orders(
                        source_order_id, source_user_id, source_product_id,
                        user_id, product_id, order_date, quantity
                   )
                   SELECT %s, %s, %s, u.user_id, p.product_id, %s, %s
                   FROM users u
                   JOIN products p
                     ON p.source_product_id = %s
                   WHERE u.source_user_id = %s
                   ON CONFLICT(source_order_id) DO UPDATE SET
                     source_user_id=EXCLUDED.source_user_id,
                     source_product_id=EXCLUDED.source_product_id,
                     order_date=EXCLUDED.order_date,
                     quantity=EXCLUDED.quantity,
                     user_id=EXCLUDED.user_id,
                     product_id=EXCLUDED.product_id""",
                [
                    (
                        o["source_order_id"],
                        o["source_user_id"],
                        o["source_product_id"],
                        o["order_date"],
                        o["quantity"],
                        o["source_product_id"],
                        o["source_user_id"],
                    )
                    for o in orders
                ],
            )
