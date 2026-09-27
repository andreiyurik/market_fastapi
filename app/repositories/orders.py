import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Order


class OrderRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def add(self, order: Order) -> Order:
        self.session.add(order)
        await self.session.flush()
        return order

    async def get(self, order_id: uuid.UUID) -> Order | None:
        return await self.session.get(Order, order_id)
