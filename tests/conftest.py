import os

# Tests run against a separate database so they never touch development data.
os.environ.setdefault("POSTGRES_DB", "app_test")

from collections.abc import AsyncIterator

import pytest
from httpx import ASGITransport, AsyncClient

from app.core.db import engine
from app.main import app
from app.models import Base


@pytest.fixture(scope="session", autouse=True)
async def database() -> AsyncIterator[None]:
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    yield
    await engine.dispose()


@pytest.fixture
async def client() -> AsyncIterator[AsyncClient]:
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        yield client


@pytest.fixture
async def product(client: AsyncClient) -> dict:
    response = await client.post("/products", json={"title": "Vintage camera", "price": "150.00"})
    assert response.status_code == 201
    return response.json()
