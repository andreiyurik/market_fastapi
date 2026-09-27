class DomainError(Exception):
    """Base class for business rule violations. Knows nothing about HTTP."""

    message = "Domain error"

    def __init__(self, message: str | None = None) -> None:
        super().__init__(message or self.message)


class NotFoundError(DomainError):
    message = "Resource not found"


class ConflictError(DomainError):
    message = "Conflict with the current state of the resource"


class ProductNotFoundError(NotFoundError):
    message = "Product not found"


class ProductNotAvailableError(ConflictError):
    message = "Product is not available for ordering"
