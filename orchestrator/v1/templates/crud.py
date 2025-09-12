"""Template CRUD utility functions for orchestrator service.

This module provides functions to retrieve, list, add, and delete templates in
the database. It wraps generic CRUD operations with templates-specific logic
and exception handling.
"""

import uuid

from sqlmodel import Session

from orchestrator.db import SessionDep
from orchestrator.v1.crud import add_item, delete_item, get_item, get_items, update_item
from orchestrator.v1.models import Template, User
from orchestrator.v1.templates.schemas import TemplateCreate, TemplateUpdate


def get_template(*, session: SessionDep, template_id: uuid.UUID) -> Template | None:
    """Retrieve a template by their unique template_id from the database.

    Args:
        session (Session): The database session dependency.
        template_id (uuid.UUID): The UUID of the template to retrieve.

    Returns:
        Template instance if found, otherwise None.

    """
    return get_item(session=session, entity=Template, id=template_id)


def get_templates(
    *, session: Session, skip: int, limit: int, sort: str, **kwargs
) -> tuple[list[Template], int]:
    """Retrieve a paginated and sorted list of templates from the database.

    The total count corresponds to the total count of returned values which may differs
    from the showed templates since they are paginated.

    Args:
        session (Session): The database session.
        skip (int): Number of templates to skip (for pagination).
        limit (int): Maximum number of templates to return.
        sort (str): Field name to sort by (prefix with '-' for descending).
        **kwargs: Additional filter parameters for narrowing the search.

    Returns:
        Tuple of (list of User instances, total count of matching templates).

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
    """Add a new template to the database.

    Args:
        session (Session): The database session.
        template (TemplateCreate): The model instance to add.
        created_by (User): The user issuing the operation.

    Returns:
        Template: The newly created DB entity.

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
    """Update a template retrieved from the database.

    Extend the existing entity with new data (ovverrides only not None values)

    Args:
        session (Session): The database session.
        template (Template): The DB entity to update.
        new_data (TemplateUpdate): The new data to update the template with.
        updated_by (User): The user issuing the operation

    Returns:
        None

    """
    return update_item(
        session=session,
        entity=Template,
        item=template,
        updated_by=updated_by,
        **new_data.model_dump(exclude_none=True),
    )


def delete_template(*, session: Session, template: Template) -> None:
    """Delete a template from the database.

    Args:
        session (Session): The database session.
        template (Template): The DB entity to delete.

    Returns:
        None

    """
    return delete_item(session=session, entity=Template, item=template)
