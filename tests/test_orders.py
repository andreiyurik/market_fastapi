import uuid

from httpx import AsyncClient


async def test_create_order_reserves_product(client: AsyncClient, product: dict) -> None:
    response = await client.post("/orders", json={"product_id": product["id"]})

    assert response.status_code == 201
    assert response.json()["product_id"] == product["id"]

    product_response = await client.get(f"/products/{product['id']}")
    assert product_response.json()["status"] == "RESERVED"


async def test_cannot_order_reserved_product(client: AsyncClient, product: dict) -> None:
    await client.post("/orders", json={"product_id": product["id"]})

    response = await client.post("/orders", json={"product_id": product["id"]})

    assert response.status_code == 409
    assert response.json() == {"detail": "Product is not available for ordering"}


async def test_order_for_missing_product_returns_404(client: AsyncClient) -> None:
    response = await client.post("/orders", json={"product_id": str(uuid.uuid4())})

    assert response.status_code == 404
    assert response.json() == {"detail": "Product not found"}


async def test_pay_order_sells_product(client: AsyncClient, product: dict) -> None:
    order = (await client.post("/orders", json={"product_id": product["id"]})).json()

    response = await client.post(f"/orders/{order['id']}/pay")

    assert response.status_code == 200
    assert response.json()["id"] == product["id"]
    assert response.json()["status"] == "SOLD"


async def test_cannot_pay_order_twice(client: AsyncClient, product: dict) -> None:
    order = (await client.post("/orders", json={"product_id": product["id"]})).json()
    await client.post(f"/orders/{order['id']}/pay")

    response = await client.post(f"/orders/{order['id']}/pay")

    assert response.status_code == 409
    assert response.json() == {"detail": "Order has already been paid"}


async def test_pay_missing_order_returns_404(client: AsyncClient) -> None:
    response = await client.post(f"/orders/{uuid.uuid4()}/pay")

    assert response.status_code == 404
    assert response.json() == {"detail": "Order not found"}


async def test_cannot_order_sold_product(client: AsyncClient, product: dict) -> None:
    order = (await client.post("/orders", json={"product_id": product["id"]})).json()
    await client.post(f"/orders/{order['id']}/pay")

    response = await client.post("/orders", json={"product_id": product["id"]})

    assert response.status_code == 409
