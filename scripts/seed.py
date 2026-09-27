"""Reset demo data: delete all orders and products, then insert sample products.

Usage: uv run python -m scripts.seed
"""

import asyncio
from decimal import Decimal

from sqlalchemy import delete

from app.core.db import SessionLocal, engine
from app.models import Order, Product

PRODUCTS = [
    ("Leica M6, 1986", "185000.00"),
    ("iPhone 15 Pro, 256 GB", "79990.00"),
    ("Nike Air Jordan 1 Chicago, 43", "42000.00"),
    ("Sony PlayStation 5", "38500.00"),
    ("Herman Miller Aeron", "65000.00"),
    ("Fujifilm X100V", "129000.00"),
    ("Nintendo Switch OLED", "24990.00"),
    ("MacBook Air M2, 16 GB", "89000.00"),
]


async def seed() -> None:
    async with SessionLocal() as session:
        await session.execute(delete(Order))
        await session.execute(delete(Product))
        session.add_all(Product(title=title, price=Decimal(price)) for title, price in PRODUCTS)
        await session.commit()
    await engine.dispose()
    print(f"Seeded {len(PRODUCTS)} products")


if __name__ == "__main__":
    asyncio.run(seed())
