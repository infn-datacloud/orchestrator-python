"""Dependencies for deployment operations in the orchestrator."""

import uuid
from typing import Annotated

from fastapi import Depends, Request

from orchestrator.exceptions import ItemNotFoundError
from orchestrator.v1.deployments.crud import get_deployment
from orchestrator.v1.models import Deployment

DeploymentDep = Annotated[Deployment | None, Depends(get_deployment)]


def deployment_required(
    request: Request, deployment_id: uuid.UUID, deployment: DeploymentDep
) -> Deployment:
    """Dependency to ensure the specified deployment exists.

    Args:
        request (Request): The current FastAPI request object.
        deployment_id (uuid.UUID): The UUID of the deployment to check.
        deployment (Deployment | None): The deployment instance if found, otherwise
            None.

    Raises:
        ItemNotFoundError: If the deployment does not exist.

    """
    if deployment is None:
        message = f"Deployment with id={deployment_id!s} does not exist"
        request.state.logger.error(message)
        raise ItemNotFoundError(message)
    return deployment


DeploymentRequiredDep = Annotated[Deployment, Depends(deployment_required)]
