from fastapi import FastAPI

from app.api.errors import register_exception_handlers
from app.api.main import api_router
from app.core.config import settings

app = FastAPI(title=settings.PROJECT_NAME)

register_exception_handlers(app)
app.include_router(api_router)
