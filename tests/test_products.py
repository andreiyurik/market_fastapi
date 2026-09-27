import uuid

from httpx import AsyncClient


async def test_create_product(client: AsyncClient) -> None:
    response = await client.post("/products", json={"title": "Sneakers", "price": "99.90"})

    assert response.status_code == 201
    body = response.json()
    assert body["title"] == "Sneakers"
    assert body["price"] == "99.90"
    assert body["status"] == "AVAILABLE"
    assert uuid.UUID(body["id"])


async def test_create_product_rejects_invalid_price(client: AsyncClient) -> None:
    response = await client.post("/products", json={"title": "Sneakers", "price": "-1"})

    assert response.status_code == 422


async def test_get_product(client: AsyncClient, product: dict) -> None:
    response = await client.get(f"/products/{product['id']}")

    assert response.status_code == 200
    assert response.json() == product


async def test_get_missing_product_returns_404(client: AsyncClient) -> None:
    response = await client.get(f"/products/{uuid.uuid4()}")

    assert response.status_code == 404
    assert response.json() == {"detail": "Product not found"}
