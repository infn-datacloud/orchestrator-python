"""Users' utility functions."""

import sqlalchemy
from sqlmodel import Session, delete, desc, func, select

from orchestrator.common.exceptions import ConflictError
from orchestrator.common.schemas import ItemID
from orchestrator.db import SessionDep
from orchestrator.v1.users.schemas import User, UserCreate


def get_user(user_id: str, session: SessionDep) -> User | None:
    """Dependency to search a user with the given user_id in the DB."""
    statement = select(User).where(User.id == user_id)
    return session.exec(statement).first()


def get_users(
    *, session: Session, skip: int, limit: int, sort: str, **kwargs
) -> tuple[list[User], int]:
    """Dependency to search a user with the given user_id in the DB.

    Apply sorting and narrowing on the search. Return also the total count of users.
    """
    if sort.startswith("-"):
        key = desc(User.__table__.c.get(sort[1:]))
    else:
        key = User.__getattribute__(sort)

    conditions = []
    for k, v in kwargs.items():
        if v is not None:
            conditions.append(User.__table__.c.get(k) == v)

    statement = (
        select(User)
        .offset(skip)
        .limit(limit)
        .order_by(key)
        .filter(sqlalchemy.and_(*conditions))
    )
    users = session.exec(statement).all()

    statement = select(func.count(User.id))
    tot_items = session.exec(statement).first()

    return users, tot_items


def add_user(*, session: Session, user: UserCreate) -> ItemID:
    """Dependecy to add a user to the DB.

    Do not check before hand if user already exists. The function lets the DB query to
    raise an error and then it catches it."""
    try:
        db_user = User(**user.model_dump())
        session.add(db_user)
        session.commit()
        return db_user
    except sqlalchemy.exc.IntegrityError as e:
        if "UNIQUE constraint failed: user.sub, user.issuer" in e.args[0]:
            raise ConflictError(
                f"User with sub '{user.sub}' and belonging to issuer "
                f"'{user.issuer}' already exists"
            ) from e


def delete_user(*, session: Session, user_id: int) -> None:
    """Dependency to delete a user with the given user_id from the DB."""
    statement = delete(User).where(User.id == user_id)
    session.exec(statement)
    session.commit()
