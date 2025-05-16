"""Custom common exceptions."""


class ConflictError(Exception):
    """Exception raised when there is a CONFLICT during a DB insertion."""

    def __init__(self, message):
        self.message = message
        super().__init__(self.message)


class ItemNotFoundError(Exception):
    """Exception raised when the target item was not foudn in the DB."""

    def __init__(self, message):
        self.message = message
        super().__init__(self.message)
