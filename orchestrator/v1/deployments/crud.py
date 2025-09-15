"""Deployment CRUD utility functions for orchestrator service.

This module provides functions to retrieve, list, add, and delete deployments in
the database. It wraps generic CRUD operations with deployments-specific logic
and exception handling.
"""

import uuid

from sqlmodel import Session

from orchestrator.db import SessionDep
from orchestrator.exceptions import ItemNotFoundError
from orchestrator.v1.crud import add_item, delete_item, get_item, get_items, update_item
from orchestrator.v1.deployments.schemas import DeploymentCreate, DeploymentUpdate
from orchestrator.v1.models import Deployment, User
from orchestrator.v1.templates.crud import get_template


def get_deployment(
    *, session: SessionDep, deployment_id: uuid.UUID
) -> Deployment | None:
    """Retrieve a deployment by their unique deployment_id from the database.

    Args:
        session (Session): The database session dependency.
        deployment_id (uuid.UUID): The UUID of the deployment to retrieve.

    Returns:
        Deployment instance if found, otherwise None.

    """
    return get_item(session=session, entity=Deployment, id=deployment_id)


def get_deployments(
    *, session: Session, skip: int, limit: int, sort: str, **kwargs
) -> tuple[list[Deployment], int]:
    """Retrieve a paginated and sorted list of deployments from the database.

    The total count corresponds to the total count of returned values which may differs
    from the showed deployments since they are paginated.

    Args:
        session (Session): The database session.
        skip (int): Number of deployments to skip (for pagination).
        limit (int): Maximum number of deployments to return.
        sort (str): Field name to sort by (prefix with '-' for descending).
        **kwargs: Additional filter parameters for narrowing the search.

    Returns:
        Tuple of (list of User instances, total count of matching deployments).

    """
    return get_items(
        session=session,
        entity=Deployment,
        skip=skip,
        limit=limit,
        sort=sort,
        **kwargs,
    )


def add_deployment(
    *, session: Session, deployment: DeploymentCreate, created_by: User
) -> Deployment:
    """Add a new deployment to the database.

    Args:
        session (Session): The database session.
        deployment (DeploymentCreate): The model instance to add.
        created_by (User): The user issuing the operation.
        template (Template): Matching template.

    Returns:
        Deployment: The newly created DB entity.

    """
    template = get_template(session=session, template_id=deployment.template_id)
    if template is None:
        message = f"Template with id={deployment.template_id!s} does not exist"
        raise ItemNotFoundError(message)
    return add_item(
        session=session,
        entity=Deployment,
        created_by=created_by,
        updated_by=created_by,
        owned_by=[created_by],
        user_group_issuer=created_by.issuer,
        template=template,
        **deployment.model_dump(),
    )


def update_deployment(
    *,
    session: Session,
    deployment: Deployment,
    new_data: DeploymentUpdate,
    updated_by: User,
) -> None:
    """Update a deployment retrieved from the database.

    Extend the existing entity with new data (ovverrides only not None values)

    Args:
        session (Session): The database session.
        deployment (Deployment): The DB entity to update.
        new_data (DeploymentUpdate): The new data to update the deployment with.
        updated_by (User): The user issuing the operation

    Returns:
        None

    """
    return update_item(
        session=session,
        entity=Deployment,
        item=deployment,
        updated_by=updated_by,
        **new_data.model_dump(exclude_none=True),
    )


def delete_deployment(
    *, session: Session, deployment: uuid.UUID, force: bool = False
) -> None:
    """Delete a deployment from the database.

    Args:
        session (Session): The database session.
        deployment (Deployment): The DB entity to delete.
        force (bool): If false, do not delete the DB entry but mark it as deleted.
            If true, delete the DB entry.

    Returns:
        None

    """
    if force:
        return delete_item(session=session, entity=Deployment, item=deployment)
    else:
        ...
