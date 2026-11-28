__all__ = ["InvalidConfigurationError", "DuplicateKeyError"]


class InvalidConfigurationError(Exception):
    """
    Indicates that a configuration file is invalid.
    """

    def __init__(self, message: str) -> None:
        super().__init__(message)


class DuplicateKeyError(Exception):
    """
    Indicates that a key is non-unique in a :py:class:`cordix.core.utils.Registry`.
    This happens if a key is shared between multiple attributes but not within
    the same attribute as this would raise a :py:class:`ValueError`.
    """

    def __init__(self, message: str) -> None:
        super().__init__(message)


class ReadOnlyError(Exception):
    """
    Indicates that a :py:class:`cordix.core.utils.Registry` is set to read-only,
    which means entries cannot be registered or unregistered.
    """

    def __init__(self, message: str) -> None:
        super().__init__(message)
