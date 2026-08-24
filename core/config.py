import os
from dataclasses import dataclass
from dotenv import load_dotenv

load_dotenv()

@dataclass(frozen=True)
class Settings:
    database_url: str | None = os.getenv("DATABASE_URL")
    seed: int = int(os.getenv("PIPELINE_SEED", "42"))
    users: int = int(os.getenv("PIPELINE_USERS", "100"))
    orders: int = int(os.getenv("PIPELINE_ORDERS", "800"))

settings = Settings()
