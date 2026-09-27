import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Order, Product, ProductStatus
from app.repositories.orders import OrderRepository
from app.repositories.products import ProductRepository
from app.schemas import OrderCreate
from app.services.exceptions import (
    OrderAlreadyPaidError,
    OrderNotFoundError,
    ProductNotAvailableError,
    ProductNotFoundError,
)


class OrderService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.products = ProductRepository(session)
        self.orders = OrderRepository(session)

    async def create(self, data: OrderCreate) -> Order:
        """Reserve the product and create an order in a single transaction."""
        product = await self.products.change_status(
            data.product_id,
            from_status=ProductStatus.AVAILABLE,
            to_status=ProductStatus.RESERVED,
        )
        if product is None:
            if await self.products.get(data.product_id) is None:
                raise ProductNotFoundError
            raise ProductNotAvailableError

        order = await self.orders.add(Order(product_id=product.id))
        await self.session.commit()
        return order

    async def pay(self, order_id: uuid.UUID) -> Product:
        """Pay for the order: the reserved product becomes SOLD."""
        order = await self.orders.get(order_id)
        if order is None:
            raise OrderNotFoundError

        product = await self.products.change_status(
            order.product_id,
            from_status=ProductStatus.RESERVED,
            to_status=ProductStatus.SOLD,
        )
        if product is None:
            raise OrderAlreadyPaidError

        await self.session.commit()
        return product
