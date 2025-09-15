"""Resource CRUD utility functions for orchestrator service.

This module provides functions to retrieve, list, add, and delete resources in
the database. It wraps generic CRUD operations with resources-specific logic
and exception handling.
"""

import uuid

from sqlmodel import Session

from orchestrator.db import SessionDep
from orchestrator.v1.crud import (
    add_item,
    delete_item,
    get_item,
    get_items,
)  # , update_item
from orchestrator.v1.deployments.resources.schemas import ResourceCreate
from orchestrator.v1.models import Deployment, Resource, User


def get_resource(*, session: SessionDep, resource_id: uuid.UUID) -> Resource | None:
    """Retrieve a resource by their unique resource_id from the database.

    Args:
        session (Session): The database session dependency.
        resource_id (uuid.UUID): The UUID of the resource to retrieve.

    Returns:
        Resource instance if found, otherwise None.

    """
    return get_item(session=session, entity=Resource, id=resource_id)


def get_resources(
    *, session: Session, skip: int, limit: int, sort: str, **kwargs
) -> tuple[list[Resource], int]:
    """Retrieve a paginated and sorted list of resources from the database.

    The total count corresponds to the total count of returned values which may differs
    from the showed resources since they are paginated.

    Args:
        session (Session): The database session.
        skip (int): Number of resources to skip (for pagination).
        limit (int): Maximum number of resources to return.
        sort (str): Field name to sort by (prefix with '-' for descending).
        **kwargs: Additional filter parameters for narrowing the search.

    Returns:
        Tuple of (list of User instances, total count of matching resources).

    """
    return get_items(
        session=session,
        entity=Resource,
        skip=skip,
        limit=limit,
        sort=sort,
        **kwargs,
    )


def add_resource(
    *,
    session: Session,
    resource: ResourceCreate,
    created_by: User,
    deployment: Deployment,
) -> Resource:
    """Add a new resource to the database.

    Args:
        session (Session): The database session.
        resource (ResourceCreate): The model instance to add.
        created_by (User): The user issuing the operation.
        deployment (Deployment): Parent deployment.

    Returns:
        Resource: The newly created DB entity.

    """
    return add_item(
        session=session,
        entity=Resource,
        created_by=created_by,
        updated_by=created_by,
        deployment=deployment,
        **resource.model_dump(),
    )


# def update_resource(
#     *,
#     session: Session,
#     resource: Resource,
#     new_data: ResourceUpdate,
#     updated_by: User,
# ) -> None:
#     """Update a resource retrieved from the database.

#     Extend the existing entity with new data (ovverrides only not None values)

#     Args:
#         session (Session): The database session.
#         resource (Resource): The DB entity to update.
#         new_data (ResourceUpdate): The new data to update the resource with.
#         updated_by (User): The user issuing the operation

#     Returns:
#         None

#     """
#     return update_item(
#         session=session,
#         entity=Resource,
#         item=resource,
#         updated_by=updated_by,
#         **new_data.model_dump(exclude_none=True),
#     )


def delete_resource(
    *, session: Session, resource: uuid.UUID, force: bool = False
) -> None:
    """Delete a resource from the database.

    Args:
        session (Session): The database session.
        resource (Resource): The DB entity to delete.
        force (bool): If false, do not delete the DB entry but mark it as deleted.
            If true, delete the DB entry.

    Returns:
        None

    """
    if force:
        return delete_item(session=session, entity=Resource, item=resource)
    else:
        ...
