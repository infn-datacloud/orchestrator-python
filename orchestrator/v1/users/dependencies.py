"""Dependencies for user-related operations in the federation manager."""

import uuid
from typing import Annotated

from fastapi import Depends, HTTPException, Request, status

from orchestrator.auth import AuthenticationDep
from orchestrator.db import SessionDep
from orchestrator.exceptions import ItemNotFoundError
from orchestrator.v1.models import User
from orchestrator.v1.users.crud import get_user, get_users

UserDep = Annotated[User | None, Depends(get_user)]


def user_required(request: Request, user_id: uuid.UUID, user: UserDep) -> User:
    """Dependency to ensure the specified identity provider exists.

    Raises an HTTP 404 error if the identity provider with the given idp_id does not
    exist.

    Args:
        request: The current FastAPI request object.
        user_id: The UUID of the user to check.
        user: The User instance if found, otherwise None.

    Raises:
        HTTPException: If the user does not exist.

    """
    if user is None:
        message = f"User with id={user_id!s} does not exist"
        request.state.logger.error(message)
        raise ItemNotFoundError(message)
    return user


UserRequiredDep = Annotated[User, Depends(user_required)]


def get_current_user(user_infos: AuthenticationDep, session: SessionDep) -> User:
    """Retrieve from the DB the user matching the user submitting the request.

    Args:
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
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No user with the given credentials was found in the DB.",
        )
    return users[0]


CurrenUserDep = Annotated[User, Depends(get_current_user)]
