"""Deployment CRUD utility functions for fed-mgr service.

This module provides functions to retrieve, list, add, and delete identity providers in
the database. It wraps generic CRUD operations with identity providers-specific logic
and exception handling.
"""

import uuid

from sqlmodel import Session

from orchestrator.db import SessionDep
from orchestrator.v1.crud import add_item, delete_item, get_item, get_items, update_item
from orchestrator.v1.deployments.schemas import DeploymentCreate, DeploymentUpdate
from orchestrator.v1.models import Deployment, User


def get_deployment(
    *, session: SessionDep, deployment_id: uuid.UUID
) -> Deployment | None:
    """Retrieve an identity provider by their unique deployment_id from the database.

    Args:
        deployment_id: The UUID of the identity provider to retrieve.
        session: The database session dependency.

    Returns:
        Deployment instance if found, otherwise None.

    """
    return get_item(session=session, entity=Deployment, id=deployment_id)


def get_deployments(
    *, session: Session, skip: int, limit: int, sort: str, **kwargs
) -> tuple[list[Deployment], int]:
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
        Tuple of (list of Deployment instances, total count of matching identity
        providers).

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
    """Add a new identity provider to the database.

    Args:
        session: The database session.
        deployment: The DeploymentCreate model instance to add.
        created_by: The User instance representing the creator of the identity provider.

    Returns:
        Deployment: The identifier of the newly created identity provider.

    """
    return add_item(
        session=session,
        entity=Deployment,
        created_by=created_by,
        updated_by=created_by,
        **deployment.model_dump(),
    )


def update_deployment(
    *,
    session: Session,
    deployment: Deployment,
    new_data: DeploymentUpdate,
    updated_by: User,
) -> None:
    """Update an identity provider by their unique deployment_id from the database.

    Completely override an deployment entity.

    Args:
        session: The database session.
        deployment: The UUID of the identity provider to update.
        new_data: The new data to update the identity provider with.
        updated_by: The User instance representing the updater of the identity provider.

    """
    return update_item(
        session=session,
        entity=Deployment,
        item=deployment,
        updated_by=updated_by,
        **new_data.model_dump(exclude_none=True),
    )


def delete_deployment(*, session: Session, deployment_id: uuid.UUID) -> None:
    """Delete a identity provider by their unique deployment_id from the database.

    Args:
        session: The database session.
        deployment_id: The UUID of the identity provider to delete.

    """
    delete_item(session=session, entity=Deployment, id=deployment_id)
