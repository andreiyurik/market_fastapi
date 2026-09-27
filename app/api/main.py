from fastapi import APIRouter

api_router = APIRouter()


@api_router.get("/health", tags=["health"])
async def health() -> dict[str, str]:
    return {"status": "ok"}
