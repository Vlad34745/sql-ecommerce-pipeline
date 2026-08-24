from dataclasses import dataclass

@dataclass
class QualityResult:
    passed: bool
    checks: list[tuple[str, bool, str]]

def validate_records(products, users, orders):
    checks = []
    checks.append(("users_not_empty", bool(users), f"{len(users)} users"))
    checks.append(("products_not_empty", bool(products), f"{len(products)} products"))
    checks.append(("orders_not_empty", bool(orders), f"{len(orders)} orders"))

    user_ids = [u["source_user_id"] for u in users]
    product_ids = [p["source_product_id"] for p in products]
    order_ids = [o["source_order_id"] for o in orders]

    checks.append(("unique_user_ids", len(user_ids) == len(set(user_ids)), "source_user_id uniqueness"))
    checks.append(("unique_product_ids", len(product_ids) == len(set(product_ids)), "source_product_id uniqueness"))
    checks.append(("unique_order_ids", len(order_ids) == len(set(order_ids)), "source_order_id uniqueness"))
    checks.append(("valid_prices", all(p["price"] >= 0 for p in products), "price >= 0"))
    checks.append(("valid_quantities", all(o["quantity"] > 0 for o in orders), "quantity > 0"))
    checks.append(("valid_user_refs", all(o["source_user_id"] in set(user_ids) for o in orders), "order users exist"))
    checks.append(("valid_product_refs", all(o["source_product_id"] in set(product_ids) for o in orders), "order products exist"))

    return QualityResult(all(ok for _, ok, _ in checks), checks)

def print_quality_report(result: QualityResult):
    print("\nDATA QUALITY")
    for name, ok, detail in result.checks:
        print(f"[{'PASS' if ok else 'FAIL'}] {name}: {detail}")
