__all__ = ["ServiceNotFoundError"]


class ServiceNotFoundError(Exception):
    """
    Indicates that a service with the given identification was not found.
    """

    def __init__(self, message: str) -> None:
        super().__init__(message)
