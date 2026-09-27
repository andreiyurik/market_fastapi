from httpx import AsyncClient

from scripts.export_openapi import OPENAPI_PATH, render_openapi


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
        "products-list_products",
        "products-get_product",
        "orders-create_order",
        "orders-pay_order",
    } <= operation_ids


def test_committed_openapi_schema_is_up_to_date() -> None:
    assert OPENAPI_PATH.read_text() == render_openapi(), (
        "openapi.json is outdated, run: uv run python -m scripts.export_openapi"
    )
