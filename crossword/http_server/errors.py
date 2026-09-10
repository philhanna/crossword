"""
API error type shared by the HTTP handlers.

Handlers raise ApiError to report a failure together with the HTTP status
that should accompany it. The request handler turns it into a JSON body of
the form {"error": "<message>"} sent with that status.
"""


class ApiError(Exception):
    """An error response: an HTTP status code plus a client-facing message."""

    def __init__(self, status: int, message: str):
        super().__init__(message)
        self.status = status
        self.message = message
