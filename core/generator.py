import random
from datetime import datetime, timedelta, timezone
from faker import Faker

PRODUCT_TEMPLATES = [
    {"source_product_id": "prod-001", "name": "Wireless Mouse", "category": "Electronics", "price": 25.0},
    {"source_product_id": "prod-002", "name": "Mechanical Keyboard", "category": "Electronics", "price": 85.0},
    {"source_product_id": "prod-003", "name": "Gaming Monitor 24'", "category": "Electronics", "price": 180.0},
    {"source_product_id": "prod-004", "name": "Leather Office Chair", "category": "Furniture", "price": 220.0},
    {"source_product_id": "prod-005", "name": "Standing Desk", "category": "Furniture", "price": 350.0},
    {"source_product_id": "prod-006", "name": "Coffee Mug", "category": "Kitchen", "price": 12.5},
    {"source_product_id": "prod-007", "name": "Stainless Steel Water Bottle", "category": "Kitchen", "price": 24.0},
    {"source_product_id": "prod-008", "name": "Running Shoes", "category": "Apparel", "price": 95.0},
    {"source_product_id": "prod-009", "name": "Cotton Hoodie", "category": "Apparel", "price": 45.0},
    {"source_product_id": "prod-010", "name": "Yoga Mat", "category": "Sports", "price": 30.0},
]

def generate_raw_data(num_users=100, num_orders=800, seed=42):
    rng = random.Random(seed)
    fake = Faker()
    fake.seed_instance(seed)

    products = PRODUCT_TEMPLATES.copy()
    users = []
    start_date = datetime(2025, 1, 1)
    for i in range(num_users):
        reg_date = start_date + timedelta(days=rng.randint(0, 500))
        users.append({
            "source_user_id": f"user-{seed}-{i+1:05d}",
            "name": fake.name(),
            "email": fake.unique.email(),
            "reg_date": reg_date.date(),
        })

    orders = []
    for i in range(num_orders):
        user_idx = rng.randrange(num_users)
        prod_idx = rng.randrange(len(products))
        reg_date = datetime.combine(users[user_idx]["reg_date"], datetime.min.time())
        order_date = reg_date + timedelta(days=rng.randint(0, 60), hours=rng.randint(0, 23))
        orders.append({
            "source_order_id": f"order-{seed}-{i+1:06d}",
            "source_user_id": users[user_idx]["source_user_id"],
            "source_product_id": products[prod_idx]["source_product_id"],
            "order_date": order_date,
            "quantity": rng.randint(1, 4),
        })
    return products, users, orders
