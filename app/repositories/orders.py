from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Order


class OrderRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def add(self, order: Order) -> Order:
        self.session.add(order)
        await self.session.flush()
        return order
