from core.generator import generate_raw_data
from core.quality import validate_records

def test_generator_is_deterministic():
    a = generate_raw_data(10, 20, seed=7)
    b = generate_raw_data(10, 20, seed=7)
    assert a == b

def test_quality_checks_pass():
    products, users, orders = generate_raw_data(20, 50, seed=1)
    result = validate_records(products, users, orders)
    assert result.passed
