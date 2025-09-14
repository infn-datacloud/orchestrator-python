"""Endpoints to manage template details."""

import uuid

from fastapi import APIRouter, Request, Response, status

from orchestrator.db import SessionDep
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
    TemplateDep,
    TemplateRequiredDep,
)
from orchestrator.v1.templates.schemas import (
    TemplateList,
    TemplateQueryDep,
    TemplateRead,
    TemplateUpdate,
)
from orchestrator.v1.users.dependencies import CurrentUserDep

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
    description="Add a new template to the DB. Check if the template's hashed version "
    "already exists in the DB. If so, the endpoint raises a 409 error.",
    status_code=status.HTTP_201_CREATED,
    responses={
        status.HTTP_409_CONFLICT: {"model": ErrorMessage},
        status.HTTP_422_UNPROCESSABLE_ENTITY: {"model": ErrorMessage},
    },
)
def create_template(
    request: Request,
    session: SessionDep,
    current_user: CurrentUserDep,
    template: TemplateCreateDep,
) -> ItemID:
    """Create a new template in the system.

    If the template already exists, returns a 409 Conflict response.
    When adding a new entry retrieve from the template's content useful metadata.

    Args:
        request (Request): The incoming HTTP request object, used for logging.
        session (Session): The database session dependency.
        current_user (User): The DB user matching the current user retrieved from the
            access token.
        template (TemplateCreate): The template data to create.

    Returns:
        ItemID: A dictionary containing the ID of the created template on success.

    Raises:
        401 Unauthorized: If the user is not authenticated (handled by dependencies).
        403 Forbidden: If the user does not have permission (handled by dependencies).
        409 Conflict: If the template already exists (handled by exception handlers).
        422 Unprocessable Entity: If the input values can't be parsed (handled by
            fastapi).

    """
    msg = "Creating template with params: "
    msg += f"{template.model_dump_json(exclude={'hash_content', 'content'})}"
    request.state.logger.info(msg)
    request.state.logger.debug(template.content)
    db_template = add_template(
        session=session, template=template, created_by=current_user
    )
    msg = "Template created: "
    msg += f"{db_template.model_dump_json(exclude={'hash_content', 'content'})}"
    request.state.logger.info(msg)
    return {"id": db_template.id}


@template_router.get(
    "/",
    summary="Retrieve templates",
    description="Retrieve a paginated list of templates. It is possible to filter and "
    "sort by any field of the entity. It is possible to paginate the returned list.",
)
def retrieve_templates(
    request: Request, session: SessionDep, params: TemplateQueryDep
) -> TemplateList:
    """Retrieve a paginated list of templates based on query parameters.

    Fetches users from the database using pagination, sorting, and additional filters
    provided in the query parameters. Returns the users in a paginated response format.

    Args:
        request (Request): The HTTP request object, used for logging and URL generation.
        session (Session): Database session dependency.
        params (TemplateQuery): Dependency containing query parameters for filtering,
            sorting, and pagination.

    Returns:
        TemplateList: A paginated list of templates matching the query parameters.

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
    description="Check if the given template's ID already exists in the DB and return "
    "it. If the template does not exist in the DB, the endpoint raises a 404 error.",
    responses={status.HTTP_404_NOT_FOUND: {"model": ErrorMessage}},
)
def retrieve_template(request: Request, template: TemplateRequiredDep) -> TemplateRead:
    """Retrieve a template by their unique identifier.

    Checks if the template exists, and returns the template object if found. If the
    template does not exist, logs an error and returns a JSON response with a 404
    status.

    Args:
        request (Request): The incoming HTTP request object.
        template (Template): The template object, if found.

    Returns:
        Template: The template object if found.

    Raises:
        401 Unauthorized: If the user is not authenticated (handled by dependencies).
        403 Forbidden: If the user does not have permission (handled by dependencies).
        404 Not Found: If the template does not exist (handled by exception handlers).

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
    description="Update the metadata of a template with the given ID in the DB. "
    "If the template does not exist raise 404 error",
    status_code=status.HTTP_204_NO_CONTENT,
    responses={
        status.HTTP_404_NOT_FOUND: {"model": ErrorMessage},
        status.HTTP_422_UNPROCESSABLE_ENTITY: {"model": ErrorMessage},
    },
)
def edit_template(
    request: Request,
    session: SessionDep,
    current_user: CurrentUserDep,
    template: TemplateRequiredDep,
    new_data: TemplateUpdate,
) -> None:
    """Update an existing template in the database with the given template ID.

    Args:
        request (Request): The current request object.
        session (Session): The database session dependency.
        current_user (User): The DB user matching the current user retrieved from the
            access token.
        template (Template): The unique identifier of the template to update.
        new_data (UserCreate): The new template data to update.

    Returns:
        None

    Raises:
        401 Unauthorized: If the user is not authenticated (handled by dependencies).
        403 Forbidden: If the user does not have permission (handled by dependencies).
        404 Not Found: If the template does not exist (handled by exception handlers).
        422 Unprocessable Entity: If the input data are not valid (handled by fastapi).

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
    summary="Delete template with given ID",
    description="Delete a template with the given ID from the DB. If the template is "
    "used by one or more deployments in the DB, they can't be deleted.",
    status_code=status.HTTP_204_NO_CONTENT,
    responses={status.HTTP_409_CONFLICT: {"model": ErrorMessage}},
)
def remove_template(
    request: Request, session: SessionDep, template_id: uuid.UUID, template: TemplateDep
) -> None:
    """Remove a template from the system by their unique identifier.

    Logs the deletion process and delegates the actual removal to the `delete_template`
    function.

    Args:
        request (Request): The HTTP request object, used for logging and request context
        session (Session): The database session dependency used to perform the
            deletion.
        template_id (uuid.UUID): The unique identifier of the template to be removed.
        template (Template | None): The DB entity to be removed.

    Returns:
        None

    Raises:
        401 Unauthorized: If the user is not authenticated (handled by dependencies).
        403 Forbidden: If the user does not have permission (handled by dependencies).
        409 Conflict: If the template has related entities and can't be deleted (handled
            by dependencies).

    """
    msg = f"Delete template with ID '{template_id!s}'"
    request.state.logger.info(msg)
    if template is not None:
        delete_template(session=session, template=template)
    msg = f"Template with ID '{template_id!s}' deleted"
    request.state.logger.info(msg)
