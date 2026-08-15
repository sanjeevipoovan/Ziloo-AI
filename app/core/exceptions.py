"""
Application exception hierarchy + FastAPI exception handler registration.

Every handled error, whatever caused it, comes back to the client in the
same shape:

    {"error": {"code": "...", "message": "...", "request_id": "..."}}

Route and service code should raise one of the MyAIException subclasses
below rather than returning ad hoc error responses. Provider-specific
failures (Hugging Face timeouts, auth errors, ...) are translated into
these at the orchestrator boundary - see app/orchestrator/execution.py -
so this module has no knowledge of any specific provider.
"""
import structlog
from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from sqlalchemy.exc import SQLAlchemyError

logger = structlog.get_logger("myai.errors")


class MyAIException(Exception):
    code = "INTERNAL_ERROR"
    status_code = 500
    message = "An unexpected error occurred"

    def __init__(self, message: str | None = None, *, code: str | None = None, status_code: int | None = None):
        self.message = message or self.message
        self.code = code or self.code
        self.status_code = status_code or self.status_code
        super().__init__(self.message)


class NotFoundError(MyAIException):
    code = "NOT_FOUND"
    status_code = 404
    message = "Resource not found"


class ConflictError(MyAIException):
    code = "CONFLICT"
    status_code = 409
    message = "Resource conflict"


class AuthenticationError(MyAIException):
    code = "AUTHENTICATION_FAILED"
    status_code = 401
    message = "Authentication failed"


class AuthorizationError(MyAIException):
    code = "FORBIDDEN"
    status_code = 403
    message = "You do not have permission to perform this action"


class ValidationAppError(MyAIException):
    code = "VALIDATION_ERROR"
    status_code = 422
    message = "Invalid request"


class RateLimitError(MyAIException):
    code = "RATE_LIMIT_EXCEEDED"
    status_code = 429
    message = "Rate limit exceeded, please slow down"


class ModelUnavailableError(MyAIException):
    code = "MODEL_UNAVAILABLE"
    status_code = 503
    message = "The selected model is temporarily unavailable"


class ProviderError(MyAIException):
    code = "PROVIDER_ERROR"
    status_code = 502
    message = "The upstream model provider returned an error"


def _request_id(request: Request) -> str:
    return getattr(request.state, "request_id", "unknown")


def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(MyAIException)
    async def handle_myai_exception(request: Request, exc: MyAIException):
        return JSONResponse(
            status_code=exc.status_code,
            content={"error": {"code": exc.code, "message": exc.message, "request_id": _request_id(request)}},
        )

    @app.exception_handler(RequestValidationError)
    async def handle_validation_error(request: Request, exc: RequestValidationError):
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content={
                "error": {
                    "code": "VALIDATION_ERROR",
                    "message": "Invalid request",
                    "request_id": _request_id(request),
                    "details": exc.errors(),
                }
            },
        )

    @app.exception_handler(SQLAlchemyError)
    async def handle_database_error(request: Request, exc: SQLAlchemyError):
        logger.error("database_error", request_id=_request_id(request), error=str(exc))
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "error": {
                    "code": "DATABASE_ERROR",
                    "message": "A database error occurred",
                    "request_id": _request_id(request),
                }
            },
        )

    @app.exception_handler(Exception)
    async def handle_unexpected_error(request: Request, exc: Exception):
        logger.exception("unhandled_exception", request_id=_request_id(request))
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "error": {
                    "code": "INTERNAL_ERROR",
                    "message": "An unexpected error occurred",
                    "request_id": _request_id(request),
                }
            },
        )
