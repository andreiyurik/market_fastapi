import uuid
from collections.abc import Sequence

from sqlalchemy import select, update
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

    async def list(self, *, limit: int, offset: int) -> Sequence[Product]:
        stmt = (
            select(Product)
            .order_by(Product.created_at.desc(), Product.id)
            .limit(limit)
            .offset(offset)
        )
        return (await self.session.scalars(stmt)).all()

    async def change_status(
        self, product_id: uuid.UUID, *, from_status: ProductStatus, to_status: ProductStatus
    ) -> Product | None:
        """Atomically move the product from `from_status` to `to_status`.

        The WHERE clause is the concurrency guard: PostgreSQL locks the row for the
        UPDATE, so of several concurrent transactions only the first one matches
        `status = from_status`. The others wait for the lock, re-check the condition,
        see the new status and update nothing. Returns None if nothing was updated.
        """
        stmt = (
            update(Product)
            .where(Product.id == product_id, Product.status == from_status)
            .values(status=to_status)
            .returning(Product)
        )
        return await self.session.scalar(stmt)
