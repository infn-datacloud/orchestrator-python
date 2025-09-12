"""Endpoints to manage deployment details."""

import uuid

from fastapi import (
    APIRouter,
    HTTPException,
    Request,
    Response,
    status,
)

from orchestrator.db import SessionDep
from orchestrator.exceptions import (
    ConflictError,
    DeleteFailedError,
    ItemNotFoundError,
    NotNullError,
)
from orchestrator.utils import add_allow_header_to_resp
from orchestrator.v1 import TEMPLATES_PREFIX
from orchestrator.v1.deployments.crud import (
    add_deployment,
    delete_deployment,
    get_deployments,
    update_deployment,
)
from orchestrator.v1.deployments.dependencies import DeploymentRequiredDep
from orchestrator.v1.deployments.schemas import (
    DeploymentCreate,
    DeploymentList,
    DeploymentQueryDep,
    DeploymentRead,
    DeploymentUpdate,
)
from orchestrator.v1.schemas import ErrorMessage, ItemID
from orchestrator.v1.templates.dependencies import TemplateRequiredDep
from orchestrator.v1.users.dependencies import CurrenUserDep

deployment_router = APIRouter(prefix=TEMPLATES_PREFIX, tags=["deployments"])


@deployment_router.options(
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
    add_allow_header_to_resp(deployment_router, response)


@deployment_router.post(
    "/",
    summary="Create a new deployment",
    description="Add a new deployment to the DB. Check if a deployment's "
    "subject, for this issuer, already exists in the DB. If the sub already exists, "
    "the endpoint raises a 409 error.",
    status_code=status.HTTP_201_CREATED,
    responses={
        status.HTTP_400_BAD_REQUEST: {"model": ErrorMessage},
        status.HTTP_409_CONFLICT: {"model": ErrorMessage},
        status.HTTP_422_UNPROCESSABLE_ENTITY: {"model": ErrorMessage},
    },
)
def create_deployment(
    request: Request,
    session: SessionDep,
    current_user: CurrenUserDep,
    template: TemplateRequiredDep,
    deployment: DeploymentCreate,
) -> ItemID:
    """Create a new deployment in the system.

    Logs the creation attempt and result. If the deployment already exists,
    returns a 409 Conflict response. If no body is given, it retrieves from the access
    token the deployment data.

    Args:
        request (Request): The incoming HTTP request object, used for logging.
        deployment (DeploymentCreate | None): The deployment data to create.
        current_user (CurrenUserDep): The DB user matching the current user retrieved
            from the access token.
        session (SessionDep): The database session dependency.
        template (DeploymentCreate | None): The deployment data to create.

    Returns:
        ItemID: A dictionary containing the ID of the created deployment on
        success.

    Raises:
        401 Unauthorized: If the user is not authenticated (handled by dependencies).
        403 Forbidden: If the user does not have permission (handled by dependencies).
        409 Conflict: If the user already exists (handled below).

    """
    msg = f"Creating deployment with params: {deployment.model_dump_json()}"
    request.state.logger.info(msg)
    request.state.logger.debug(deployment.content)
    try:
        db_deployment = add_deployment(
            session=session, deployment=deployment, created_by=current_user
        )
    except ConflictError as e:
        request.state.logger.error(e.message)
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail=e.message
        ) from e
    except NotNullError as e:
        request.state.logger.error(e.message)
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=e.message
        ) from e
    msg = f"Deployment created: {db_deployment.model_dump_json()}"
    request.state.logger.info(msg)
    return {"id": db_deployment.id}


@deployment_router.get(
    "/",
    summary="Retrieve deployments",
    description="Retrieve a paginated list of deployments.",
)
def retrieve_deployments(
    request: Request, session: SessionDep, params: DeploymentQueryDep
) -> DeploymentList:
    """Retrieve a paginated list of deployments based on query parameters.

    Logs the query parameters and the number of deployments retrieved. Fetches
    deployments from the database using pagination, sorting, and additional
    filters provided in the query parameters. Returns the deployments in a
    paginated response format.

    Args:
        request (Request): The HTTP request object, used for logging and URL generation.
        params (DeploymentQueryDep): Dependency containing query parameters for
            filtering, sorting, and pagination.
        session (SessionDep): Database session dependency.

    Returns:
        DeploymentList: A paginated list of deployments matching the query
            parameters.

    Raises:
        401 Unauthorized: If the user is not authenticated (handled by dependencies).
        403 Forbidden: If the user does not have permission (handled by dependencies).

    """
    msg = f"Retrieve deployments. Query params: {params.model_dump_json()}"
    request.state.logger.info(msg)
    deployments, tot_items = get_deployments(
        session=session,
        skip=(params.page - 1) * params.size,
        limit=params.size,
        sort=params.sort,
        **params.model_dump(exclude={"page", "size", "sort"}, exclude_none=True),
    )
    msg = f"{tot_items} retrieved deployments: "
    msg += f"{[deployment.model_dump_json() for deployment in deployments]}"
    request.state.logger.info(msg)
    new_deployments = []
    for deployment in deployments:
        new_deployment = DeploymentRead(
            **deployment.model_dump(),  # Does not return created_by and updated_by
            created_by=deployment.created_by_id,
            updated_by=deployment.created_by_id,
            base_url=str(request.url),
        )
        new_deployments.append(new_deployment)
    return DeploymentList(
        data=new_deployments,
        resource_url=str(request.url),
        page_number=params.page,
        page_size=params.size,
        tot_items=tot_items,
    )


@deployment_router.get(
    "/{deployment_id}",
    summary="Retrieve deployment with given ID",
    description="Check if the given deployment's ID already exists in the DB "
    "and return it. If the deployment does not exist in the DB, the endpoint "
    "raises a 404 error.",
    responses={status.HTTP_404_NOT_FOUND: {"model": ErrorMessage}},
)
def retrieve_deployment(
    request: Request, deployment: DeploymentRequiredDep
) -> DeploymentRead:
    """Retrieve a deployment by their unique identifier.

    Logs the retrieval attempt, checks if the deployment exists, and returns the
    deployment object if found. If the deployment does not exist, logs an
    error and returns a JSON response with a 404 status.

    Args:
        request (Request): The incoming HTTP request object.
        deployment_id (uuid.UUID): The unique identifier of the deployment to retrieve.
        deployment (Deployment | None): The deployment object, if found.

    Returns:
        Deployment: The deployment object if found.
        JSONResponse: A 404 response if the deployment does not exist.

    Raises:
        401 Unauthorized: If the user is not authenticated (handled by dependencies).
        403 Forbidden: If the user does not have permission (handled by dependencies).
        404 Not Found: If the user does not exist (handled below).

    """
    msg = (
        f"Deployment with ID '{deployment.id!s}' found: {deployment.model_dump_json()}"
    )
    request.state.logger.info(msg)
    deployment = DeploymentRead(
        **deployment.model_dump(),  # Does not return created_by and updated_by
        created_by=deployment.created_by_id,
        updated_by=deployment.created_by_id,
        base_url=str(request.url),
    )
    return deployment


@deployment_router.patch(
    "/{deployment_id}",
    summary="Update deployment with the given id",
    description="Update a deployment with the given id in the DB",
    status_code=status.HTTP_204_NO_CONTENT,
    responses={
        status.HTTP_400_BAD_REQUEST: {"model": ErrorMessage},
        status.HTTP_404_NOT_FOUND: {"model": ErrorMessage},
        status.HTTP_422_UNPROCESSABLE_ENTITY: {"model": ErrorMessage},
    },
)
def edit_deployment(
    request: Request,
    session: SessionDep,
    current_user: CurrenUserDep,
    deployment_id: uuid.UUID,
    new_deployment: DeploymentUpdate,
) -> None:
    """Update an existing deployment in the database with the given deployment ID.

    Args:
        request (Request): The current request object.
        deployment_id (uuid.UUID): The unique identifier of the deployment to update.
        new_deployment (UserCreate): The new deployment data to update.
        session (SessionDep): The database session dependency.
        current_user (CurrenUserDep): The DB user matching the current user retrieved
            from the access token.

    Raises:
        HTTPException: If the deployment is not found or another update error
        occurs.

    """
    msg = f"Update deployment with ID '{deployment_id!s}'"
    request.state.logger.info(msg)
    try:
        update_deployment(
            session=session,
            deployment_id=deployment_id,
            new_deployment=new_deployment,
            updated_by=current_user,
        )
    except ItemNotFoundError as e:
        request.state.logger.error(e.message)
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=e.message
        ) from e
    except ConflictError as e:
        request.state.logger.error(e.message)
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail=e.message
        ) from e
    except NotNullError as e:
        request.state.logger.error(e.message)
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=e.message
        ) from e
    msg = f"Deployment with ID '{deployment_id!s}' updated"
    request.state.logger.info(msg)


@deployment_router.delete(
    "/{deployment_id}",
    summary="Delete deployment with given sub",
    description="Delete a deployment with the given subject, for this issuer, "
    "from the DB.",
    status_code=status.HTTP_204_NO_CONTENT,
    responses={status.HTTP_400_BAD_REQUEST: {"model": ErrorMessage}},
)
def remove_deployment(
    request: Request,
    session: SessionDep,
    deployment_id: uuid.UUID,
    force: bool,
    unsecure: bool,
) -> None:
    """Remove a deployment from the system by their unique identifier.

    Logs the deletion process and delegates the actual removal to the
    `delete_deployment` function.

    Args:
        request (Request): The HTTP request object, used for logging and request context
        deployment_id (uuid.UUID): The unique identifier of the deployment to be removed
        session (SessionDep): The database session dependency used to perform the
            deletion.
        force (uuid.UUID): The unique identifier of the deployment to be removed
        unsecure (uuid.UUID): The unique identifier of the deployment to be removed

    Returns:
        None

    Raises:
        401 Unauthorized: If the user is not authenticated (handled by dependencies).
        403 Forbidden: If the user does not have permission (handled by dependencies).

    """
    msg = f"Delete deployment with ID '{deployment_id!s}'"
    request.state.logger.info(msg)
    try:
        delete_deployment(session=session, deployment_id=deployment_id)
    except DeleteFailedError as e:
        request.state.logger.error(e.message)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=e.message
        ) from e
    msg = f"Deployment with ID '{deployment_id!s}' deleted"
    request.state.logger.info(msg)
