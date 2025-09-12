"""User CRUD utility functions for orchestrator service.

This module provides functions to retrieve, list, add, and delete users in the database.
It wraps generic CRUD operations with user-specific logic and exception handling.
"""

import uuid

from sqlmodel import Session

from orchestrator.db import SessionDep
from orchestrator.v1.crud import add_item, delete_item, get_item, get_items, update_item
from orchestrator.v1.models import User
from orchestrator.v1.users.schemas import UserCreate, UserUpdate

FAKE_USER_NAME = "fake_name"
FAKE_USER_EMAIL = "fake@email.com"
FAKE_USER_SUBJECT = "fake_sub"
FAKE_USER_ISSUER = "http://fake.iss.it"


def get_user(*, session: SessionDep, user_id: uuid.UUID) -> User | None:
    """Retrieve a user by their unique user_id from the database.

    Args:
        session (Session): The database session dependency.
        user_id (uuid.UUID): The UUID of the user to retrieve.

    Returns:
        User instance if found, otherwise None.

    """
    return get_item(session=session, entity=User, id=user_id)


def get_users(
    *, session: Session, skip: int, limit: int, sort: str, **kwargs
) -> tuple[list[User], int]:
    """Retrieve a paginated and sorted list of users from the database.

    The total count corresponds to the total count of returned values which may differs
    from the showed users since they are paginated.

    Args:
        session (Session): The database session.
        skip (int): Number of users to skip (for pagination).
        limit (int): Maximum number of users to return.
        sort (str): Field name to sort by (prefix with '-' for descending).
        **kwargs: Additional filter parameters for narrowing the search.

    Returns:
        Tuple of (list of User instances, total count of matching users).

    """
    return get_items(
        session=session, entity=User, skip=skip, limit=limit, sort=sort, **kwargs
    )


def add_user(*, session: Session, user: UserCreate) -> User:
    """Add a new user to the database.

    Args:
        session (Session): The database session.
        user (UserCreate): The model instance to add.

    Returns:
        User: The newly created DB entity.

    """
    return add_item(session=session, entity=User, **user.model_dump())


def update_user(*, session: Session, user: User, new_data: UserUpdate) -> None:
    """Update a user retrieved from the database.

    Extend the existing entity with new data (ovverrides only not None values)

    Args:
        session (Session): The database session.
        user (User): The DB entity to update.
        new_data (UserUpdate): The new data to update the user with.

    Returns:
        None

    """
    return update_item(
        session=session,
        entity=User,
        item=user,
        **new_data.model_dump(exclude_none=True),
    )


def delete_user(*, session: Session, user: User) -> None:
    """Delete a user from the database.

    Args:
        session (Session): The database session.
        user (User): The DB entity to delete.

    Returns:
        None

    """
    return delete_item(session=session, entity=User, item=user)


def create_fake_user(session: Session) -> User:
    """Create a fake user in the database for testing or development purposes.

    If the fake user already exists return the ID of the existing user.

    Args:
        session (Session): The database session.

    Returns:
        User: the DB entry of the fake user.

    """
    users, tot_items = get_users(
        session=session,
        skip=0,
        limit=1,
        sort="-created_at",
        name=FAKE_USER_NAME,
        issuer=FAKE_USER_ISSUER,
    )
    if tot_items == 0:
        return add_user(
            session=session,
            user=UserCreate(
                name=FAKE_USER_NAME,
                email=FAKE_USER_EMAIL,
                sub=FAKE_USER_SUBJECT,
                issuer=FAKE_USER_ISSUER,
            ),
        )
    return users[0]


def delete_fake_user(session: Session) -> None:
    """Delete the fake user in the database used for testing or development purposes.

    Args:
        session (Session): The database session.

    Returns:
        None

    """
    users, tot_items = get_users(
        session=session,
        skip=0,
        limit=1,
        sort="-created_at",
        name=FAKE_USER_NAME,
        issuer=FAKE_USER_ISSUER,
    )
    if tot_items > 0:
        return delete_user(session=session, user=users[0])
