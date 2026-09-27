import uuid
from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field

from app.models import ProductStatus


class ProductCreate(BaseModel):
    title: str = Field(min_length=1, max_length=255, examples=["iPhone 15 Pro, 256 GB"])
    price: Decimal = Field(gt=0, max_digits=12, decimal_places=2, examples=["79990.00"])


class ProductRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    title: str
    price: Decimal
    status: ProductStatus
    created_at: datetime


class OrderCreate(BaseModel):
    product_id: uuid.UUID


class OrderRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    product_id: uuid.UUID
    created_at: datetime


class ErrorResponse(BaseModel):
    detail: str
