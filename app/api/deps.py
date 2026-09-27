from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_session
from app.services.orders import OrderService
from app.services.products import ProductService

SessionDep = Annotated[AsyncSession, Depends(get_session)]


def get_product_service(session: SessionDep) -> ProductService:
    return ProductService(session)


ProductServiceDep = Annotated[ProductService, Depends(get_product_service)]


def get_order_service(session: SessionDep) -> OrderService:
    return OrderService(session)


OrderServiceDep = Annotated[OrderService, Depends(get_order_service)]
