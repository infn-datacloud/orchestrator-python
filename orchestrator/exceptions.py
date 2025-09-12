"""Custom common exceptions."""

from fastapi import FastAPI, HTTPException, Request, status
from fastapi.responses import JSONResponse
from flaat.exceptions import FlaatUnauthenticated


class ConflictError(Exception):
    """Exception raised when there is a CONFLICT during a DB insertion."""

    def __init__(self, message: str):
        """Initialize ConflictError with a specific error message."""
        self.message = message
        super().__init__(self.message)


class NotNullError(Exception):
    """Exception raised when a None value is not acceptale during DB insertion."""

    def __init__(self, message):
        """Initialize NotNullError with a specific error message."""
        self.message = message
        super().__init__(self.message)


class ItemNotFoundError(Exception):
    """Exception raised when the target ID does not match a user in the DB."""

    def __init__(self, message: str):
        """Initialize ItemNotFoundError with a specific error message."""
        self.message = message
        super().__init__(self.message)


class DeleteFailedError(Exception):
    """Exception raised when the delete operations has no effect."""

    def __init__(self):
        """Initialize DeleteFailedError with a specific error message."""
        self.message = "Deletion failed"
        super().__init__(self.message)


def add_exception_handlers(app: FastAPI) -> None:
    """Add exception handlers to app."""

    @app.exception_handler(HTTPException)
    def http_exception_handler(request: Request, exc: HTTPException):
        """Handle HTTPException errors by returning a JSON response.

        The new object contains the exception's status code and detail.

        Args:
            request (Request): The incoming HTTP request that caused the exception.
            exc (HTTPException): The HTTP exception instance.

        Returns:
            JSONResponse: A JSON response with the status code and detail of the
                exception.

        """
        return JSONResponse(
            status_code=exc.status_code,
            content={"status": exc.status_code, "detail": exc.detail},
        )

    @app.exception_handler(ItemNotFoundError)
    def item_not_found_exception_handler(request: Request, exc: ItemNotFoundError):
        """Handle ItemNotFoundError errors by returning a JSON response.

        The new object contains the exception's status code and detail.

        Args:
            request (Request): The incoming HTTP request that caused the exception.
            exc (ItemNotFoundError): The exception instance.

        Returns:
            JSONResponse: A JSON response with the status code and detail of the
                exception.

        """
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content={"status": status.HTTP_404_NOT_FOUND, "detail": exc.message},
        )

    @app.exception_handler(ConflictError)
    def conflict_exception_handler(request: Request, exc: ConflictError):
        """Handle ConflictError errors by returning a JSON response.

        The new object contains the exception's status code and detail.

        Args:
            request (Request): The incoming HTTP request that caused the exception.
            exc (ConflictError): The exception instance.

        Returns:
            JSONResponse: A JSON response with the status code and detail of the
                exception.

        """
        return JSONResponse(
            status_code=status.HTTP_409_CONFLICT,
            content={"status": status.HTTP_409_CONFLICT, "detail": exc.message},
        )

    @app.exception_handler(DeleteFailedError)
    def delete_failed_exception_handler(request: Request, exc: DeleteFailedError):
        """Handle DeleteFailedError errors by returning a JSON response.

        The new object contains the exception's status code and detail.

        Args:
            request (Request): The incoming HTTP request that caused the exception.
            exc (DeleteFailedError): The exception instance.

        Returns:
            JSONResponse: A JSON response with the status code and detail of the
                exception.

        """
        return JSONResponse(
            status_code=status.HTTP_409_CONFLICT,
            content={"status": status.HTTP_409_CONFLICT, "detail": exc.message},
        )

    @app.exception_handler(FlaatUnauthenticated)
    def unauthenticated_exception_handler(request: Request, exc: FlaatUnauthenticated):
        """Handle FlaatUnauthenticated errors by returning a JSON response.

        The new object contains the exception's status code and detail.

        Args:
            request (Request): The incoming HTTP request that caused the exception.
            exc (FlaatUnauthenticated): The exception instance.

        Returns:
            JSONResponse: A JSON response with the status code and detail of the
                exception.

        """
        return JSONResponse(
            status_code=status.HTTP_403_FORBIDDEN,
            content={"status": status.HTTP_403_FORBIDDEN, "detail": exc.render()},
        )
