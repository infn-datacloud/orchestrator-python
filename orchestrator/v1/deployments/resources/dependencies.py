"""Dependencies for resource operations in the orchestrator."""

import uuid
from typing import Annotated

from fastapi import Depends, Request

from orchestrator.exceptions import ItemNotFoundError
from orchestrator.v1.deployments.resources.crud import get_resource
from orchestrator.v1.models import Resource

ResourceDep = Annotated[Resource | None, Depends(get_resource)]


def resource_required(
    request: Request, resource_id: uuid.UUID, resource: ResourceDep
) -> Resource:
    """Dependency to ensure the specified resource exists.

    Args:
        request (Request): The current FastAPI request object.
        resource_id (uuid.UUID): The UUID of the resource to check.
        resource (Resource | None): The resource instance if found, otherwise
            None.

    Raises:
        ItemNotFoundError: If the resource does not exist.

    """
    if resource is None:
        message = f"Resource with id={resource_id!s} does not exist"
        request.state.logger.error(message)
        raise ItemNotFoundError(message)
    return resource


ResourceRequiredDep = Annotated[Resource, Depends(resource_required)]
