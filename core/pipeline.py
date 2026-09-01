import argparse

from core.analytics import run_query
from core.config import settings
from core.db_manager import init_db
from core.generator import generate_raw_data
from core.loaders import load_to_postgres, load_to_sqlite
from core.postgres_manager import init_postgres_db
from core.quality import print_quality_report, validate_records


def run_pipeline(users=None, orders=None, seed=None, reset=False, skip_postgres=False):
    users = settings.users if users is None else users
    orders = settings.orders if orders is None else orders
    seed = settings.seed if seed is None else seed

    print(f"[PIPELINE] users={users}, orders={orders}, seed={seed}, reset={reset}")

    products, user_rows, order_rows = generate_raw_data(users, orders, seed)

    quality = validate_records(products, user_rows, order_rows)
    print_quality_report(quality)
    if not quality.passed:
        raise RuntimeError("Data quality checks failed. Pipeline stopped.")

    # Normal runs keep existing data and use UPSERTs. --reset is the explicit
    # destructive mode used for a clean/full reload.
    init_db(reset=reset)
    load_to_sqlite(products, user_rows, order_rows)
    print(f"[SQLITE] Loaded/upserted {len(user_rows)} users and {len(order_rows)} orders.")

    if skip_postgres:
        print("[PIPELINE] Completed successfully (SQLite only).")
        return

    init_postgres_db(reset=reset)
    load_to_postgres(products, user_rows, order_rows)
    print(f"[POSTGRES] Loaded/upserted {len(user_rows)} users and {len(order_rows)} orders.")

    print("\nSALES KPI")
    print(run_query("sales").to_string(index=False))
    print("\nTOP CUSTOMERS")
    print(run_query("ltv").to_string(index=False))
    print("\nCATEGORY PERFORMANCE")
    print(run_query("category").to_string(index=False))
    print("\nCOHORT RETENTION")
    print(run_query("cohort").to_string(index=False))
    print("\n[PIPELINE] Completed successfully.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Idempotent e-commerce ETL pipeline")
    parser.add_argument("--users", type=int, default=None)
    parser.add_argument("--orders", type=int, default=None)
    parser.add_argument("--seed", type=int, default=None)
    parser.add_argument("--reset", action="store_true", help="Drop and recreate databases before loading")
    parser.add_argument("--skip-postgres", action="store_true", help="Run local SQLite stage only")
    args = parser.parse_args()
    run_pipeline(args.users, args.orders, args.seed, args.reset, args.skip_postgres)
