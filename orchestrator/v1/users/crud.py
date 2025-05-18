"""Users' utility functions."""

import sqlalchemy
from sqlmodel import Session

from orchestrator.common.crud import add_item, delete_item, get_item, get_items
from orchestrator.common.exceptions import ConflictError
from orchestrator.common.schemas import ItemID
from orchestrator.db import SessionDep
from orchestrator.v1.users.schemas import User, UserCreate


def get_user(user_id: str, session: SessionDep) -> User | None:
    """Search a user with the given user_id in the DB."""
    return get_item(session=session, entity=User, item_id=user_id)


def get_users(
    *, session: Session, skip: int, limit: int, sort: str, **kwargs
) -> tuple[list[User], int]:
    """Search a user with the given user_id in the DB.

    Apply sorting and narrowing on the search. Return also the total count of users.
    """
    return get_items(
        session=session, entity=User, skip=skip, limit=limit, sort=sort, **kwargs
    )


def add_user(*, session: Session, user: UserCreate) -> ItemID:
    """Add a user to the DB.

    Do not check before hand if user already exists. The function lets the DB query to
    raise an error and then it catches it."""
    try:
        return add_item(session=session, entity=User, item=user)
    except sqlalchemy.exc.IntegrityError as e:
        if "UNIQUE constraint failed: user.sub, user.issuer" in e.args[0]:
            raise ConflictError(
                f"User with sub '{user.sub}' and belonging to issuer "
                f"'{user.issuer}' already exists"
            ) from e


def delete_user(*, session: Session, user_id: int) -> None:
    """Delete a user with the given user_id from the DB."""
    delete_item(session=session, entity=User, item_id=user_id)
