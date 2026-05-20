from dotenv import load_dotenv

import os

load_dotenv()

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+psycopg://fastapi:fastapi@localhost:5432/fastapi_learning",
)