"""Custom common exceptions."""


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
