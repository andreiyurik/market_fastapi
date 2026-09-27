import uuid

from sqlalchemy import update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Product, ProductStatus


class ProductRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def add(self, product: Product) -> Product:
        self.session.add(product)
        await self.session.flush()
        return product

    async def get(self, product_id: uuid.UUID) -> Product | None:
        return await self.session.get(Product, product_id)

    async def reserve(self, product_id: uuid.UUID) -> Product | None:
        """Atomically switch the product from AVAILABLE to RESERVED.

        The WHERE clause is the concurrency guard: PostgreSQL locks the row for the
        UPDATE, so of several concurrent transactions only the first one matches
        `status = AVAILABLE`. The others wait for the lock, re-check the condition,
        see RESERVED and update nothing. Returns None if the product was not reserved.
        """
        stmt = (
            update(Product)
            .where(Product.id == product_id, Product.status == ProductStatus.AVAILABLE)
            .values(status=ProductStatus.RESERVED)
            .returning(Product)
        )
        return await self.session.scalar(stmt)
