"""Endpoints to manage User details."""

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, Request, Response, Security, status
from fastapi.responses import JSONResponse

from orchestrator.auth import has_admin_access, has_user_access
from orchestrator.common.exceptions import ConflictError
from orchestrator.common.schemas import ErrorMessage, ItemID
from orchestrator.common.utils import add_allow_header_to_resp
from orchestrator.db import SessionDep
from orchestrator.v1.users.crud import add_user, delete_user, get_user, get_users
from orchestrator.v1.users.schemas import User, UserCreate, UserList, UserQueryDep

user_router = APIRouter(prefix="/users", tags=["users"])


@user_router.options(
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
    add_allow_header_to_resp(user_router, response)


@user_router.post(
    "/",
    responses={
        status.HTTP_409_CONFLICT: {"model": ErrorMessage}
    },  # TODO: Add 401, 403 and others? Standardize response model?
    summary="Create a new user",
    description="Add a new user to the DB. Check if a user's subject, for this issuer, "
    "already exists in the DB. If the sub already exists, the endpoint raises a 409 "
    "error.",
    status_code=status.HTTP_201_CREATED,
    dependencies=[Security(has_user_access)],
)
def create_user(
    request: Request,
    user: UserCreate,
    session: SessionDep,
) -> ItemID:
    """Create a new user in the system.

    Logs the creation attempt and result. If the user already exists, returns a 409
    Conflict response.

    Args:
        request (Request): The incoming HTTP request object, used for logging.
        user (UserCreate): The user data to create.
        session (SessionDep): The database session dependency.

    Returns:
        ItemID: A dictionary containing the ID of the created user on success.
        JSONResponse: A 409 Conflict response if the user already exists.

    """
    try:
        request.state.logger.info(
            "Creating user with params: %s", user.model_dump(exclude_none=True)
        )
        db_user = add_user(session=session, user=user)
        request.state.logger.info("User created: %s", repr(db_user))
        return {"id": db_user.id}
    except ConflictError as e:
        request.state.logger.error(e.message)
        return JSONResponse(
            status_code=status.HTTP_409_CONFLICT,
            content={"title": "User already exists", "message": e.message},
        )


@user_router.get(
    "/",
    summary="Retrieve users",
    description="Retrieve a paginated list of users.",
    dependencies=[Security(has_user_access)],
)
def retrieve_users(
    request: Request, params: UserQueryDep, session: SessionDep
) -> UserList:
    """Retrieve a paginated list of users based on query parameters.

    Logs the query parameters and the number of users retrieved. Fetches users from the
    database using pagination, sorting, and additional filters provided in the query
    parameters. Returns the users in a paginated response format.

    Args:
        request (Request): The HTTP request object, used for logging and URL generation.
        params (UserQueryDep): Dependency containing query parameters for filtering,
            sorting, and pagination.
        session (SessionDep): Database session dependency.

    Returns:
        UserList: A paginated list of users matching the query parameters.

    """
    request.state.logger.info(
        "Retrieve users. Query params: %s", params.model_dump(exclude_none=True)
    )
    users, tot_items = get_users(
        session=session,
        skip=(params.page - 1) * params.size,
        limit=params.size,
        sort=params.sort,
        **params.model_dump(exclude={"page", "size", "sort"}, exclude_none=True),
    )
    request.state.logger.info("%d retrieved users: %s", tot_items, repr(users))
    return UserList(
        data=users,
        resource_url=str(request.url),
        page_number=params.page,
        page_size=params.size,
        tot_items=tot_items,
    )


# @user_router.head(
#     "/{user_id}",
#     response_model=None,
#     responses={status.HTTP_404_NOT_FOUND: {"model": None}},
#     summary="Check user'sub exists",
#     description="Check if a user's subject, for this issuer, already exists in the DB"
# )
@user_router.get(
    "/{user_id}",
    responses={status.HTTP_404_NOT_FOUND: {"model": ErrorMessage}},
    summary="Retrieve user with given sub",
    description="Check if a user's subject, for this issuer, already exists in the DB "
    "and return it. If the user does not exist in the DB, the endpoint raises a 404 "
    "error.",
    dependencies=[Security(has_user_access)],
)
def retrieve_user(
    request: Request,
    user_id: uuid.UUID,
    user: Annotated[User | None, Depends(get_user)],
) -> User:
    """Retrieve a user by their unique identifier.

    Logs the retrieval attempt, checks if the user exists, and returns the user object
    if found. If the user does not exist, logs an error and returns a JSON response with
    a 404 status.

    Args:
        request (Request): The incoming HTTP request object.
        user_id (uuid.UUID): The unique identifier of the user to retrieve.
        user (User | None): The user object, if found, or None.

    Returns:
        User: The user object if found.
        JSONResponse: A 404 response if the user does not exist.

    """
    request.state.logger.info("Retrieve user with ID '%s'", str(user_id))
    if user is None:
        message = f"User with sub '{user_id!s}' does not exist"
        request.state.logger.error(message)
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content={"title": "User not found", "message": message},
        )
    request.state.logger.info("User with ID '%s' found: %s", str(user_id), repr(user))
    return user


@user_router.delete(
    "/{user_id}",
    summary="Delete user with given sub",
    description="Delete a user with the given subject, for this issuer, from the DB.",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Security(has_admin_access)],
)
def remove_user(request: Request, user_id: uuid.UUID, session: SessionDep) -> None:
    """Remove a user from the system by their unique identifier.

    Logs the deletion process and delegates the actual removal to the `delete_user`
    function.

    Args:
        request (Request): The HTTP request object, used for logging and request context
        user_id (uuid.UUID): The unique identifier of the user to be removed.
        session (SessionDep): The database session dependency used to perform the
            deletion.

    Returns:
        None

    """
    request.state.logger.info("Delete user with ID '%s'", str(user_id))
    delete_user(session=session, user_id=user_id)
    request.state.logger.info("User with ID '%s' deleted", str(user_id))
