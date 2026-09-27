"""Export the OpenAPI schema to openapi.json for frontend client generation.

Usage: uv run python -m scripts.export_openapi
"""

import json
from pathlib import Path

from app.main import app

OPENAPI_PATH = Path(__file__).resolve().parent.parent / "openapi.json"


def render_openapi() -> str:
    return json.dumps(app.openapi(), indent=2, ensure_ascii=False) + "\n"


if __name__ == "__main__":
    OPENAPI_PATH.write_text(render_openapi())
    print(f"OpenAPI schema written to {OPENAPI_PATH}")
