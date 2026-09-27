from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Order
from app.repositories.orders import OrderRepository
from app.repositories.products import ProductRepository
from app.schemas import OrderCreate
from app.services.exceptions import ProductNotAvailableError, ProductNotFoundError


class OrderService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.products = ProductRepository(session)
        self.orders = OrderRepository(session)

    async def create(self, data: OrderCreate) -> Order:
        """Reserve the product and create an order in a single transaction."""
        product = await self.products.reserve(data.product_id)
        if product is None:
            if await self.products.get(data.product_id) is None:
                raise ProductNotFoundError
            raise ProductNotAvailableError

        order = await self.orders.add(Order(product_id=product.id))
        await self.session.commit()
        return order
