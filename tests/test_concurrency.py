import asyncio

from httpx import AsyncClient
from sqlalchemy import func, select, text

from app.core.db import SessionLocal, engine
from app.models import Order

CONCURRENT_BUYERS = 20


async def warm_up_connection_pool() -> None:
    """Open pooled connections upfront, as in a long-running server.

    With a cold pool the first request finishes while the others are still
    connecting to PostgreSQL, so the requests would never actually overlap.
    """

    async def ping() -> None:
        async with engine.connect() as connection:
            await connection.execute(text("SELECT 1"))

    await asyncio.gather(*(ping() for _ in range(engine.pool.size())))


async def test_only_one_concurrent_order_reserves_product(
    client: AsyncClient, product: dict
) -> None:
    await warm_up_connection_pool()

    responses = await asyncio.gather(
        *(
            client.post("/orders", json={"product_id": product["id"]})
            for _ in range(CONCURRENT_BUYERS)
        )
    )

    status_codes = sorted(response.status_code for response in responses)
    assert status_codes == [201] + [409] * (CONCURRENT_BUYERS - 1)

    async with SessionLocal() as session:
        orders_count = await session.scalar(
            select(func.count()).select_from(Order).where(Order.product_id == product["id"])
        )
    assert orders_count == 1
