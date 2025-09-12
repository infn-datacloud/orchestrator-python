"""Template CRUD utility functions for fed-mgr service.

This module provides functions to retrieve, list, add, and delete identity providers in
the database. It wraps generic CRUD operations with identity providers-specific logic
and exception handling.
"""

import uuid

from sqlmodel import Session

from orchestrator.db import SessionDep
from orchestrator.v1.crud import add_item, delete_item, get_item, get_items, update_item
from orchestrator.v1.models import Template, User
from orchestrator.v1.templates.schemas import TemplateCreate, TemplateUpdate


def get_template(*, session: SessionDep, template_id: uuid.UUID) -> Template | None:
    """Retrieve an identity provider by their unique template_id from the database.

    Args:
        template_id: The UUID of the identity provider to retrieve.
        session: The database session dependency.

    Returns:
        Template instance if found, otherwise None.

    """
    return get_item(session=session, entity=Template, id=template_id)


def get_templates(
    *, session: Session, skip: int, limit: int, sort: str, **kwargs
) -> tuple[list[Template], int]:
    """Retrieve a paginated and sorted list of identity providers from the database.

    The total count corresponds to the total count of returned values which may differs
    from the showed identity providers since they are paginated.

    Args:
        session: The database session.
        skip: Number of identity providers to skip (for pagination).
        limit: Maximum number of identity providers to return.
        sort: Field name to sort by (prefix with '-' for descending).
        **kwargs: Additional filter parameters for narrowing the search.

    Returns:
        Tuple of (list of Template instances, total count of matching identity
        providers).

    """
    return get_items(
        session=session,
        entity=Template,
        skip=skip,
        limit=limit,
        sort=sort,
        **kwargs,
    )


def add_template(
    *, session: Session, template: TemplateCreate, created_by: User
) -> Template:
    """Add a new identity provider to the database.

    Args:
        session: The database session.
        template: The TemplateCreate model instance to add.
        created_by: The User instance representing the creator of the identity provider.

    Returns:
        Template: The identifier of the newly created identity provider.

    """
    return add_item(
        session=session,
        entity=Template,
        created_by=created_by,
        updated_by=created_by,
        **template.model_dump(),
    )


def update_template(
    *,
    session: Session,
    template: Template,
    new_data: TemplateUpdate,
    updated_by: User,
) -> None:
    """Update an identity provider by their unique template_id from the database.

    Completely override an template entity.

    Args:
        session: The database session.
        template: The UUID of the identity provider to update.
        new_data: The new data to update the identity provider with.
        updated_by: The User instance representing the updater of the identity provider.

    """
    return update_item(
        session=session,
        entity=Template,
        item=template,
        updated_by=updated_by,
        **new_data.model_dump(exclude_none=True),
    )


def delete_template(*, session: Session, template_id: uuid.UUID) -> None:
    """Delete a identity provider by their unique template_id from the database.

    Args:
        session: The database session.
        template_id: The UUID of the identity provider to delete.

    """
    delete_item(session=session, entity=Template, id=template_id)
