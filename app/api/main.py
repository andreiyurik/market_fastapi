from fastapi import APIRouter

from app.api.routes import products

api_router = APIRouter()
api_router.include_router(products.router)


@api_router.get("/health", tags=["health"])
async def health() -> dict[str, str]:
    return {"status": "ok"}
