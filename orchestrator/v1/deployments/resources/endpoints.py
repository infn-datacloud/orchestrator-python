"""Endpoints to manage resource details."""

from fastapi import APIRouter, Depends, Request, Response, status

from orchestrator.db import SessionDep
from orchestrator.utils import add_allow_header_to_resp
from orchestrator.v1 import DEPLOYMENTS_PREFIX, RESOURCES_PREFIX
from orchestrator.v1.deployments.dependencies import (
    DeploymentRequiredDep,
    deployment_required,
)
from orchestrator.v1.deployments.resources.crud import get_resources
from orchestrator.v1.deployments.resources.dependencies import ResourceRequiredDep
from orchestrator.v1.deployments.resources.schemas import (
    ResourceList,
    ResourceQueryDep,
    ResourceRead,
)
from orchestrator.v1.schemas import ErrorMessage

resource_router = APIRouter(
    prefix=DEPLOYMENTS_PREFIX + "/{deployment_id}" + {RESOURCES_PREFIX},
    tags=["resources"],
)


@resource_router.options(
    "/",
    summary="List available endpoints for this resource",
    description="List available endpoints for this resource in the 'Allow' header.",
    status_code=status.HTTP_204_NO_CONTENT,
)
def available_methods(response: Response) -> None:
    """Add the HTTP 'Allow' header to the response.

    Args:
        response (Response): The HTTP response object to which the 'Allow' header will
            be added.

    Returns:
        None

    """
    add_allow_header_to_resp(resource_router, response)


@resource_router.get(
    "/",
    summary="Retrieve resources",
    description="Retrieve a paginated list of resources.",
)
def retrieve_resources(
    request: Request,
    session: SessionDep,
    params: ResourceQueryDep,
    deployment: DeploymentRequiredDep,
) -> ResourceList:
    """Retrieve a paginated list of resources based on query parameters.

    Logs the query parameters and the number of resources retrieved. Fetches
    resources from the database using pagination, sorting, and additional
    filters provided in the query parameters. Returns the resources in a
    paginated response format.

    Args:
        request (Request): The HTTP request object, used for logging and URL generation.
        params (ResourceQueryDep): Dependency containing query parameters for
            filtering, sorting, and pagination.
        session (SessionDep): Database session dependency.
        deployment (Deployment): Parent deployment

    Returns:
        ResourceList: A paginated list of resources matching the query
            parameters.

    Raises:
        401 Unauthorized: If the user is not authenticated (handled by dependencies).
        403 Forbidden: If the user does not have permission (handled by dependencies).

    """
    msg = f"Retrieve resources. Query params: {params.model_dump_json()}"
    request.state.logger.info(msg)
    resources, tot_items = get_resources(
        session=session,
        skip=(params.page - 1) * params.size,
        limit=params.size,
        sort=params.sort,
        deployment_id=deployment.id,
        **params.model_dump(exclude={"page", "size", "sort"}, exclude_none=True),
    )
    msg = f"{tot_items} retrieved resources: "
    msg += f"{[resource.model_dump_json() for resource in resources]}"
    request.state.logger.info(msg)
    new_resources = []
    for resource in resources:
        new_resource = ResourceRead(
            **resource.model_dump(),  # Does not return created_by and updated_by
            created_by=resource.created_by_id,
            updated_by=resource.created_by_id,
            base_url=str(request.url),
        )
        new_resources.append(new_resource)
    return ResourceList(
        data=new_resources,
        resource_url=str(request.url),
        page_number=params.page,
        page_size=params.size,
        tot_items=tot_items,
    )


@resource_router.get(
    "/{resource_id}",
    summary="Retrieve resource with given ID",
    description="Check if the given resource's ID already exists in the DB "
    "and return it. If the resource does not exist in the DB, the endpoint "
    "raises a 404 error.",
    dependencies=[Depends(deployment_required)],
    responses={status.HTTP_404_NOT_FOUND: {"model": ErrorMessage}},
)
def retrieve_resource(request: Request, resource: ResourceRequiredDep) -> ResourceRead:
    """Retrieve a resource by their unique identifier.

    Logs the retrieval attempt, checks if the resource exists, and returns the
    resource object if found. If the resource does not exist, logs an
    error and returns a JSON response with a 404 status.

    Args:
        request (Request): The incoming HTTP request object.
        resource_id (uuid.UUID): The unique identifier of the resource to retrieve.
        resource (Resource | None): The resource object, if found.

    Returns:
        Resource: The resource object if found.
        JSONResponse: A 404 response if the resource does not exist.

    Raises:
        401 Unauthorized: If the user is not authenticated (handled by dependencies).
        403 Forbidden: If the user does not have permission (handled by dependencies).
        404 Not Found: If the user does not exist (handled below).

    """
    msg = f"Resource with ID '{resource.id!s}' found: {resource.model_dump_json()}"
    request.state.logger.info(msg)
    resource = ResourceRead(
        **resource.model_dump(),  # Does not return created_by and updated_by
        created_by=resource.created_by_id,
        updated_by=resource.created_by_id,
    )
    return resource
