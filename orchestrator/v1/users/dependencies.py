"""Dependencies for user operations in the orchestrator."""

import uuid
from typing import Annotated, Literal

from fastapi import Depends, Request

from orchestrator.auth import AuthenticationDep
from orchestrator.db import SessionDep
from orchestrator.exceptions import ItemNotFoundError
from orchestrator.v1.models import User
from orchestrator.v1.users.crud import get_user, get_users

UserDep = Annotated[User | None, Depends(get_user)]


def get_current_user(
    request: Request, user_infos: AuthenticationDep, session: SessionDep
) -> User:
    """Retrieve from the DB the user matching the user submitting the request.

    Args:
        request (Request): The current FastAPI request object.
        user_infos: The authentication dependency containing user information.
        session: The database session dependency.

    Returns:
        User instance if found, otherwise None.

    """
    users, count = get_users(
        session=session,
        skip=0,
        limit=1,
        sort="-created_at",
        sub=user_infos.user_info["sub"],
        issuer=user_infos.user_info["iss"],
    )
    if count == 0:
        msg = "No user with the given credentials was found in the DB."
        request.state.logger.error(msg)
        raise ItemNotFoundError(msg)
    return users[0]


CurrentUserDep = Annotated[User, Depends(get_current_user)]


def user_required(
    request: Request,
    user_id: uuid.UUID | Literal["me"],
    current_user: CurrentUserDep,
    user: UserDep,
) -> User:
    """Dependency to ensure the specified user exists.

    Args:
        request (Request): The current FastAPI request object.
        user_id (uuid.UUID): The UUID of the user to check.
        current_user (User): The user performing the operation.
        user (User | None): The user instance if found, otherwise None.

    Raises:
        ItemNotFoundError: If the user does not exist.

    """
    if user_id == "me":
        return current_user
    if user is None:
        msg = f"User with id={user_id!s} does not exist"
        request.state.logger.error(msg)
        raise ItemNotFoundError(msg)
    return user


UserRequiredDep = Annotated[User, Depends(user_required)]
