"""Reset demo data: delete all orders and products, then insert sample products.

Usage: uv run python -m scripts.seed
"""

import asyncio
from decimal import Decimal

from sqlalchemy import delete

from app.core.db import SessionLocal, engine
from app.models import Order, Product

# Assortment modelled on a typical resale store: electronics, fur, jewelry, appliances,
# watches, kids' goods and accessories.
PRODUCTS = [
    ("iPhone 16 Pro Max 256GB", "77770.00"),
    ("Ноутбук Acer Nitro 5", "30030.00"),
    ("MacBook Pro 15 (2019)", "28878.00"),
    ("Ноутбук ASUS VivoBook 15", "18198.00"),
    ("Наушники HOCO W55 Plus", "2490.00"),
    ("Шуба норковая KALYAEV", "21690.00"),
    ("Пальто Alberta Ferretti", "19999.00"),
    ("Кольцо золотое 585 с бриллиантом", "24500.00"),
    ("Серьги золотые 585 с топазом", "15990.00"),
    ("Фен профессиональный M7", "3499.00"),
    ("Аэрогриль Xiaomi Smart Air Fryer", "5990.00"),
    ("Apple Watch Series 9 45mm", "21990.00"),
    ("Casio G-Shock GA-2100", "7990.00"),
    ("Коляска Cybex Priam", "34900.00"),
    ("Конструктор LEGO Technic 42115", "18990.00"),
    ("Сумка Furla Metropolis", "12990.00"),
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
