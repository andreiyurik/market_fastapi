import uuid
from typing import Annotated

from fastapi import APIRouter, Query, status

from app.api.deps import ProductServiceDep
from app.schemas import ErrorResponse, ProductCreate, ProductRead

router = APIRouter(prefix="/products", tags=["products"])


@router.post("", status_code=status.HTTP_201_CREATED)
async def create_product(data: ProductCreate, service: ProductServiceDep) -> ProductRead:
    """Create a product. New products are always `AVAILABLE`."""
    product = await service.create(data)
    return ProductRead.model_validate(product)


@router.get("")
async def list_products(
    service: ProductServiceDep,
    limit: Annotated[int, Query(ge=1, le=100)] = 50,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> list[ProductRead]:
    """List products, newest first."""
    products = await service.list(limit=limit, offset=offset)
    return [ProductRead.model_validate(product) for product in products]


@router.get(
    "/{product_id}",
    responses={status.HTTP_404_NOT_FOUND: {"model": ErrorResponse}},
)
async def get_product(product_id: uuid.UUID, service: ProductServiceDep) -> ProductRead:
    product = await service.get(product_id)
    return ProductRead.model_validate(product)
