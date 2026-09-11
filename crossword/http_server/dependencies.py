"""
Shared FastAPI dependencies.

Routes ask for the wired application container and the current user id through
these, so nothing in a route reaches into module-level state. Tests replace
either one with app.dependency_overrides.
"""

from typing import Annotated

from fastapi import Depends, Request

from crossword.wiring import AppContainer

# The app has no login yet; every request acts as this user.
CURRENT_USER = {"id": 1}


def get_container(request: Request) -> AppContainer:
    """Return the container of use cases that was wired at startup."""
    return request.app.state.container


def get_user_id() -> int:
    """Return the id of the user making the request."""
    return CURRENT_USER["id"]


Container = Annotated[AppContainer, Depends(get_container)]
UserId = Annotated[int, Depends(get_user_id)]
