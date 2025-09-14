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


class IdentityProviderConnectionError(Exception):
    """Exception raised when connection with the IDP fails."""

    def __init__(self, message: str):
        """Initialize IdentityProviderConnectionError with a specific error message."""
        self.message = message
        super().__init__(self.message)


class VaultConnectionError(Exception):
    """Exception raised when connection with the IDP fails."""

    def __init__(self, message: str):
        """Initialize VaultConnectionError with a specific error message."""
        self.message = message
        super().__init__(self.message)


class ConfigurationError(Exception):
    """Exception raised when failing to retrieve information from settings."""

    def __init__(self, message: str):
        """Initialize ConfigurationError with a specific error message."""
        self.message = message
        super().__init__(self.message)


def add_exception_handlers(app: FastAPI) -> None:
    """Add exception handlers to app."""

    @app.exception_handler(HTTPException)
    def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
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
    def item_not_found_exception_handler(
        request: Request, exc: ItemNotFoundError
    ) -> JSONResponse:
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
    def conflict_exception_handler(
        request: Request, exc: ConflictError
    ) -> JSONResponse:
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
    def delete_failed_exception_handler(
        request: Request, exc: DeleteFailedError
    ) -> JSONResponse:
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
    def unauthenticated_exception_handler(
        request: Request, exc: FlaatUnauthenticated
    ) -> JSONResponse:
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

    @app.exception_handler(IdentityProviderConnectionError)
    def idp_connection_failed_handler(
        request: Request, exc: IdentityProviderConnectionError
    ) -> JSONResponse:
        """Handle IdentityProviderConnectionError errors by returning a JSON response.

        The new object contains the exception's status code and detail.

        Args:
            request (Request): The incoming HTTP request that caused the exception.
            exc (IdentityProviderConnectionError): The exception instance.

        Returns:
            JSONResponse: A JSON response with the status code and detail of the
                exception.

        """
        return JSONResponse(
            status_code=status.HTTP_504_GATEWAY_TIMEOUT,
            content={"status": status.HTTP_504_GATEWAY_TIMEOUT, "detail": exc.message},
        )

    @app.exception_handler(VaultConnectionError)
    def vault_connection_failed_handler(
        request: Request, exc: VaultConnectionError
    ) -> JSONResponse:
        """Handle VaultConnectionError errors by returning a JSON response.

        The new object contains the exception's status code and detail.

        Args:
            request (Request): The incoming HTTP request that caused the exception.
            exc (VaultConnectionError): The exception instance.

        Returns:
            JSONResponse: A JSON response with the status code and detail of the
                exception.

        """
        return JSONResponse(
            status_code=status.HTTP_504_GATEWAY_TIMEOUT,
            content={"status": status.HTTP_504_GATEWAY_TIMEOUT, "detail": exc.message},
        )
