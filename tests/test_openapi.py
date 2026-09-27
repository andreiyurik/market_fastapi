from httpx import AsyncClient


async def test_openapi_exposes_stable_operation_ids(client: AsyncClient) -> None:
    response = await client.get("/openapi.json")

    assert response.status_code == 200
    operation_ids = {
        operation["operationId"]
        for path in response.json()["paths"].values()
        for operation in path.values()
    }
    assert {
        "products-create_product",
        "products-get_product",
        "orders-create_order",
        "orders-pay_order",
    } <= operation_ids
