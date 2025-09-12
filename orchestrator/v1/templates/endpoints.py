"""Endpoints to manage template details."""

import uuid

from fastapi import (
    APIRouter,
    HTTPException,
    Request,
    Response,
    status,
)

from orchestrator.db import SessionDep
from orchestrator.exceptions import NotNullError
from orchestrator.utils import add_allow_header_to_resp
from orchestrator.v1 import TEMPLATES_PREFIX
from orchestrator.v1.schemas import ErrorMessage, ItemID
from orchestrator.v1.templates.crud import (
    add_template,
    delete_template,
    get_templates,
    update_template,
)
from orchestrator.v1.templates.dependencies import (
    TemplateCreateDep,
    TemplateRequiredDep,
)
from orchestrator.v1.templates.schemas import (
    TemplateList,
    TemplateQueryDep,
    TemplateRead,
    TemplateUpdate,
)
from orchestrator.v1.users.dependencies import CurrenUserDep

template_router = APIRouter(prefix=TEMPLATES_PREFIX, tags=["templates"])


@template_router.options(
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
    add_allow_header_to_resp(template_router, response)


@template_router.post(
    "/",
    summary="Create a new template",
    description="Add a new template to the DB. Check if a template's "
    "subject, for this issuer, already exists in the DB. If the sub already exists, "
    "the endpoint raises a 409 error.",
    status_code=status.HTTP_201_CREATED,
    responses={
        status.HTTP_400_BAD_REQUEST: {"model": ErrorMessage},
        status.HTTP_409_CONFLICT: {"model": ErrorMessage},
        status.HTTP_422_UNPROCESSABLE_ENTITY: {"model": ErrorMessage},
    },
)
def create_template(
    request: Request,
    session: SessionDep,
    current_user: CurrenUserDep,
    template: TemplateCreateDep,
) -> ItemID:
    """Create a new template in the system.

    Logs the creation attempt and result. If the template already exists,
    returns a 409 Conflict response. If no body is given, it retrieves from the access
    token the template data.

    Args:
        request (Request): The incoming HTTP request object, used for logging.
        template (TemplateCreate | None): The template data to create.
        current_user (CurrenUserDep): The DB user matching the current user retrieved
            from the access token.
        session (SessionDep): The database session dependency.

    Returns:
        ItemID: A dictionary containing the ID of the created template on
        success.

    Raises:
        401 Unauthorized: If the user is not authenticated (handled by dependencies).
        403 Forbidden: If the user does not have permission (handled by dependencies).
        409 Conflict: If the user already exists (handled below).

    """
    msg = "Creating template with params: "
    msg += f"{template.model_dump_json(exclude={'hash_content', 'content'})}"
    request.state.logger.info(msg)
    request.state.logger.debug(template.content)
    try:
        db_template = add_template(
            session=session, template=template, created_by=current_user
        )
    except NotNullError as e:
        request.state.logger.error(e.message)
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=e.message
        ) from e
    msg = "Template created: "
    msg += f"{db_template.model_dump_json(exclude={'hash_content', 'content'})}"
    request.state.logger.info(msg)
    return {"id": db_template.id}


@template_router.get(
    "/",
    summary="Retrieve templates",
    description="Retrieve a paginated list of templates.",
)
def retrieve_templates(
    request: Request, session: SessionDep, params: TemplateQueryDep
) -> TemplateList:
    """Retrieve a paginated list of templates based on query parameters.

    Logs the query parameters and the number of templates retrieved. Fetches
    templates from the database using pagination, sorting, and additional
    filters provided in the query parameters. Returns the templates in a
    paginated response format.

    Args:
        request (Request): The HTTP request object, used for logging and URL generation.
        params (TemplateQueryDep): Dependency containing query parameters for
            filtering, sorting, and pagination.
        session (SessionDep): Database session dependency.

    Returns:
        TemplateList: A paginated list of templates matching the query
            parameters.

    Raises:
        401 Unauthorized: If the user is not authenticated (handled by dependencies).
        403 Forbidden: If the user does not have permission (handled by dependencies).

    """
    msg = f"Retrieve templates. Query params: {params.model_dump_json()}"
    request.state.logger.info(msg)
    templates, tot_items = get_templates(
        session=session,
        skip=(params.page - 1) * params.size,
        limit=params.size,
        sort=params.sort,
        **params.model_dump(exclude={"page", "size", "sort"}, exclude_none=True),
    )
    msg = f"{tot_items} retrieved templates: "
    msg += f"{[template.model_dump_json() for template in templates]}"
    request.state.logger.info(msg)
    new_templates = []
    for template in templates:
        new_template = TemplateRead(
            **template.model_dump(),  # Does not return created_by and updated_by
            created_by=template.created_by_id,
            updated_by=template.created_by_id,
            base_url=str(request.url),
        )
        new_templates.append(new_template)
    return TemplateList(
        data=new_templates,
        resource_url=str(request.url),
        page_number=params.page,
        page_size=params.size,
        tot_items=tot_items,
    )


@template_router.get(
    "/{template_id}",
    summary="Retrieve template with given ID",
    description="Check if the given template's ID already exists in the DB "
    "and return it. If the template does not exist in the DB, the endpoint "
    "raises a 404 error.",
    responses={status.HTTP_404_NOT_FOUND: {"model": ErrorMessage}},
)
def retrieve_template(request: Request, template: TemplateRequiredDep) -> TemplateRead:
    """Retrieve a template by their unique identifier.

    Logs the retrieval attempt, checks if the template exists, and returns the
    template object if found. If the template does not exist, logs an
    error and returns a JSON response with a 404 status.

    Args:
        request (Request): The incoming HTTP request object.
        template_id (uuid.UUID): The unique identifier of the template to retrieve.
        template (Template | None): The template object, if found.

    Returns:
        Template: The template object if found.
        JSONResponse: A 404 response if the template does not exist.

    Raises:
        401 Unauthorized: If the user is not authenticated (handled by dependencies).
        403 Forbidden: If the user does not have permission (handled by dependencies).
        404 Not Found: If the user does not exist (handled below).

    """
    msg = f"Template with ID '{template.id!s}' found: {template.model_dump_json()}"
    request.state.logger.info(msg)
    template = TemplateRead(
        **template.model_dump(),  # Does not return created_by and updated_by
        created_by=template.created_by_id,
        updated_by=template.created_by_id,
        base_url=str(request.url),
    )
    return template


@template_router.patch(
    "/{template_id}",
    summary="Update template with the given id",
    description="Update a template with the given id in the DB",
    status_code=status.HTTP_204_NO_CONTENT,
    responses={
        status.HTTP_400_BAD_REQUEST: {"model": ErrorMessage},
        status.HTTP_404_NOT_FOUND: {"model": ErrorMessage},
        status.HTTP_422_UNPROCESSABLE_ENTITY: {"model": ErrorMessage},
    },
)
def edit_template(
    request: Request,
    session: SessionDep,
    current_user: CurrenUserDep,
    template: TemplateRequiredDep,
    new_data: TemplateUpdate,
) -> None:
    """Update an existing template in the database with the given template ID.

    Args:
        request (Request): The current request object.
        session (SessionDep): The database session dependency.
        template (uuid.UUID): The unique identifier of the template to update.
        new_data (UserCreate): The new template data to update.
        current_user (CurrenUserDep): The DB user matching the current user retrieved
            from the access token.

    Raises:
        HTTPException: If the template is not found or another update error
        occurs.

    """
    msg = f"Update template with ID '{template.id!s}'"
    request.state.logger.info(msg)
    update_template(
        session=session, template=template, new_data=new_data, updated_by=current_user
    )
    msg = f"Template with ID '{template.id!s}' updated"
    request.state.logger.info(msg)


@template_router.delete(
    "/{template_id}",
    summary="Delete template with given sub",
    description="Delete a template with the given subject, for this issuer, "
    "from the DB.",
    status_code=status.HTTP_204_NO_CONTENT,
    responses={status.HTTP_400_BAD_REQUEST: {"model": ErrorMessage}},
)
def remove_template(
    request: Request, session: SessionDep, template_id: uuid.UUID
) -> None:
    """Remove a template from the system by their unique identifier.

    Logs the deletion process and delegates the actual removal to the `delete_template`
    function.

    Args:
        request (Request): The HTTP request object, used for logging and request context
        template_id (uuid.UUID): The unique identifier of the template to be removed
        session (SessionDep): The database session dependency used to perform the
            deletion.

    Returns:
        None

    Raises:
        401 Unauthorized: If the user is not authenticated (handled by dependencies).
        403 Forbidden: If the user does not have permission (handled by dependencies).

    """
    msg = f"Delete template with ID '{template_id!s}'"
    request.state.logger.info(msg)
    delete_template(session=session, template_id=template_id)
    msg = f"Template with ID '{template_id!s}' deleted"
    request.state.logger.info(msg)
