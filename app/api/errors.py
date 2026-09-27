from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse

from app.services.exceptions import ConflictError, DomainError, NotFoundError

STATUS_CODES: dict[type[DomainError], int] = {
    NotFoundError: status.HTTP_404_NOT_FOUND,
    ConflictError: status.HTTP_409_CONFLICT,
}


async def domain_error_handler(request: Request, exc: Exception) -> JSONResponse:
    status_code = next(
        (code for error, code in STATUS_CODES.items() if isinstance(exc, error)),
        status.HTTP_400_BAD_REQUEST,
    )
    return JSONResponse(status_code=status_code, content={"detail": str(exc)})


def register_exception_handlers(app: FastAPI) -> None:
    app.add_exception_handler(DomainError, domain_error_handler)
