"""Custom exceptions for the query engine.

Defines domain-specific exception types for query execution errors.
"""


class QueryTimeoutError(Exception):
    """Raised when a query exceeds the configured timeout."""

    def __init__(self, query_name: str, timeout_sec: int) -> None:
        """Initialise with query name and timeout.

        Args:
            query_name: Name or first 100 chars of the SQL query.
            timeout_sec: The timeout that was exceeded.
        """
        self.query_name = query_name
        self.timeout_sec = timeout_sec
        super().__init__(
            f"Query '{query_name}' exceeded timeout of {timeout_sec}s"
        )


class QueryNotFoundError(Exception):
    """Raised when a named query file cannot be found."""

    def __init__(self, query_name: str) -> None:
        """Initialise with query name.

        Args:
            query_name: The query name that was not found.
        """
        self.query_name = query_name
        super().__init__(f"Query file not found: {query_name}.sql")


class InvalidParameterError(Exception):
    """Raised when query parameters are invalid or missing."""

    def __init__(self, message: str) -> None:
        """Initialise with error message.

        Args:
            message: Description of the parameter error.
        """
        super().__init__(message)
