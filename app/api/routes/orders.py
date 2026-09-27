from fastapi import APIRouter, status

from app.api.deps import OrderServiceDep
from app.schemas import ErrorResponse, OrderCreate, OrderRead

router = APIRouter(prefix="/orders", tags=["orders"])


@router.post(
    "",
    status_code=status.HTTP_201_CREATED,
    responses={
        status.HTTP_404_NOT_FOUND: {"model": ErrorResponse, "description": "Product not found"},
        status.HTTP_409_CONFLICT: {
            "model": ErrorResponse,
            "description": "Product is already reserved or sold",
        },
    },
)
async def create_order(data: OrderCreate, service: OrderServiceDep) -> OrderRead:
    """Create an order and reserve the product (`AVAILABLE` → `RESERVED`)."""
    order = await service.create(data)
    return OrderRead.model_validate(order)
