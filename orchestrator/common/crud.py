"""Create Read Update and Delete generic functions."""

from typing import TypeVar

import sqlalchemy
from sqlmodel import Session, SQLModel, delete, desc, func, select

from orchestrator.common.schemas import ItemID

Entity = TypeVar("Entity", bound=ItemID)
CreateModel = TypeVar("CreateModel", bound=SQLModel)


def get_conditions(*, entity: type[Entity], **kwargs) -> list:
    """Build the conditions list used to filter out items in the query."""
    conditions = []
    for k, v in kwargs.items():
        if k == "created_before":
            conditions.append(entity.created_at <= v)
        elif k == "updated_before":
            conditions.append(entity.updated_at <= v)
        elif k == "created_after":
            conditions.append(entity.created_at >= v)
        elif k == "updated_after":
            conditions.append(entity.updated_at >= v)
        elif isinstance(v, str):
            conditions.append(entity.__table__.c.get(k).icontains(v))
        elif isinstance(v, (int, float)):
            if k.endswith("_lte"):
                conditions.append(entity.__table__.c.get(k) <= v)
            elif k.endswith("_gte"):
                conditions.append(entity.__table__.c.get(k) >= v)
            else:
                conditions.append(entity.__table__.c.get(k) == v)
    return conditions


def get_item(*, entity: type[Entity], session: Session, item_id: str) -> Entity | None:
    """Dependency to search a item with the given item_id in the DB."""
    statement = select(entity).where(entity.id == item_id)
    return session.exec(statement).first()


def get_items(
    *,
    entity: type[Entity],
    session: Session,
    skip: int,
    limit: int,
    sort: str,
    **kwargs,
) -> tuple[list[Entity], int]:
    """Dependency to search a item with the given item_id in the DB.

    Apply sorting and narrowing on the search. Return also the total count of items.
    """
    if sort.startswith("-"):
        key = desc(entity.__table__.c.get(sort[1:]))
    else:
        key = entity.__getattribute__(sort)

    conditions = get_conditions(entity=entity, **kwargs)

    statement = (
        select(entity)
        .offset(skip)
        .limit(limit)
        .order_by(key)
        .filter(sqlalchemy.and_(*conditions))
    )
    items = session.exec(statement).all()

    statement = select(func.count(entity.id)).filter(sqlalchemy.and_(*conditions))
    tot_items = session.exec(statement).first()

    return items, tot_items


def add_item(*, entity: type[Entity], session: Session, item: CreateModel) -> Entity:
    """Dependecy to add a item to the DB.

    Do not check before hand if item already exists. The function lets the DB query to
    raise an error and then it catches it."""
    db_item = entity(**item.model_dump())
    session.add(db_item)
    session.commit()
    return db_item


def delete_item(*, entity: type[Entity], session: Session, item_id: int) -> None:
    """Dependency to delete a item with the given item_id from the DB."""
    statement = delete(entity).where(entity.id == item_id)
    session.exec(statement)
    session.commit()
