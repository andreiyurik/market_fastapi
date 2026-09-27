import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Product
from app.repositories.products import ProductRepository
from app.schemas import ProductCreate
from app.services.exceptions import ProductNotFoundError


class ProductService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.products = ProductRepository(session)

    async def create(self, data: ProductCreate) -> Product:
        product = await self.products.add(Product(title=data.title, price=data.price))
        await self.session.commit()
        return product

    async def get(self, product_id: uuid.UUID) -> Product:
        product = await self.products.get(product_id)
        if product is None:
            raise ProductNotFoundError
        return product
