from core.quality import validate_records


def test_catches_duplicate_source_ids():
    products = [{"source_product_id": 1, "price": 10.0}]
    users = [
        {"source_user_id": 1},
        {"source_user_id": 1},  # duplicate
    ]
    orders = [{"source_order_id": 1, "source_user_id": 1, "source_product_id": 1, "quantity": 1}]

    result = validate_records(products, users, orders)

    assert not result.passed
    checks = dict((name, ok) for name, ok, _ in result.checks)
    assert checks["unique_user_ids"] is False


def test_catches_negative_price():
    products = [{"source_product_id": 1, "price": -5.0}]
    users = [{"source_user_id": 1}]
    orders = [{"source_order_id": 1, "source_user_id": 1, "source_product_id": 1, "quantity": 1}]

    result = validate_records(products, users, orders)

    assert not result.passed
    checks = dict((name, ok) for name, ok, _ in result.checks)
    assert checks["valid_prices"] is False


def test_catches_orphan_order_reference():
    products = [{"source_product_id": 1, "price": 10.0}]
    users = [{"source_user_id": 1}]
    orders = [{"source_order_id": 1, "source_user_id": 999, "source_product_id": 1, "quantity": 1}]

    result = validate_records(products, users, orders)

    assert not result.passed
    checks = dict((name, ok) for name, ok, _ in result.checks)
    assert checks["valid_user_refs"] is False