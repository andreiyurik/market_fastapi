from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.routing import APIRoute

from app.api.errors import register_exception_handlers
from app.api.main import api_router
from app.core.config import settings

DESCRIPTION = """Reservation and purchase API for a resale marketplace.
Each product exists in a single copy: `AVAILABLE` → `RESERVED` → `SOLD`."""

OPENAPI_TAGS = [
    {"name": "products", "description": "Create and read products."},
    {"name": "orders", "description": "Reserve a product with an order and pay for it."},
    {"name": "health", "description": "Service health check."},
]


def generate_operation_id(route: APIRoute) -> str:
    """Stable operationIds (`products-create_product`) give clean names in generated clients."""
    return f"{route.tags[0]}-{route.name}"


app = FastAPI(
    title=settings.PROJECT_NAME,
    description=DESCRIPTION,
    version="0.1.0",
    openapi_tags=OPENAPI_TAGS,
    generate_unique_id_function=generate_operation_id,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.BACKEND_CORS_ORIGINS,
    allow_methods=["*"],
    allow_headers=["*"],
)

register_exception_handlers(app)
app.include_router(api_router)
