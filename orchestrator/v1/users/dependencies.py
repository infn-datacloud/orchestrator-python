"""Endpoints to manage User details."""

from datetime import datetime
from uuid import uuid4

from orchestrator.common.exceptions import ConflictError
from orchestrator.common.schemas import ItemID
from orchestrator.v1.users.schemas import UserCreate, UserSingle


def get_user(user_id: str) -> UserSingle | None:
    """Dependency to search a user with the given user_id in the DB."""
    # TODO search in the DB
    return None


def get_users(*, skip: int, limit: int, sort: str) -> tuple[list[UserSingle], int]:
    """Dependency to search a user with the given user_id in the DB.

    Apply sorting and narrowing on the search."""
    # TODO search in the DB
    return [], 0


def add_user(user: UserCreate) -> ItemID:
    """Dependecy to add a user to the DB.

    Do not check before hand if user already exists. The function lets the DB query to
    raise an error and then it catches it."""
    try:
        # TODO add user to the DB.
        db_user = UserSingle(**user, id=uuid4(), created_at=datetime.now())
        return ItemID(id=db_user.id)
    except:
        # TODO parse error to verify the problem is a conflict
        raise ConflictError(
            f"User with sub '{user.sub}' and belonging to issuer "
            f"'{user.issuer}' already exists"
        ) from None

def delete_user(user_id: str) -> None:
    """Dependency to delete a user with the given user_id from the DB."""
    # TODO delete user from the DB
