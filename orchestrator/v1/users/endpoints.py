"""Endpoints to manage User details."""

import uuid
from typing import Annotated, Literal

from fastapi import APIRouter, Body, HTTPException, Request, Response, status
from pydantic import AfterValidator, Field

from orchestrator.auth import AuthenticationDep
from orchestrator.config import SettingsDep
from orchestrator.db import SessionDep
from orchestrator.exceptions import ConflictError
from orchestrator.utils import (
    add_allow_header_to_resp,
    create_ssh_keys,
    verify_public_ssh_key,
)
from orchestrator.v1 import USERS_PREFIX
from orchestrator.v1.schemas import ErrorMessage, ItemID
from orchestrator.v1.users.crud import (
    add_user,
    delete_user,
    get_users,
    update_user,
)
from orchestrator.v1.users.dependencies import UserDep, UserRequiredDep
from orchestrator.v1.users.schemas import (
    UserCreate,
    UserList,
    UserQueryDep,
    UserRead,
    UserUpdate,
)
from orchestrator.vault import delete_private_key, store_private_key

user_router = APIRouter(prefix=USERS_PREFIX, tags=["users"])


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
    summary="Create a new user from user's token",
    description="Add a new user to the DB. Check if a user's subject, for this issuer, "
    "already exists in the DB. If the sub already exists, the endpoint raises a 409 "
    "error.",
    status_code=status.HTTP_201_CREATED,
    responses={
        status.HTTP_409_CONFLICT: {"model": ErrorMessage},
        status.HTTP_422_UNPROCESSABLE_ENTITY: {"model": ErrorMessage},
    },
)
def create_me(
    request: Request, session: SessionDep, current_user_infos: AuthenticationDep
) -> ItemID:
    """From token crendentials, create a new user in the system.

    If the user already exists, returns a 409 Conflict response. It retrieves from the
    access token the user data.

    Args:
        request (Request): The incoming HTTP request object, used for logging.
        session (Session): The database session dependency.
        current_user_infos (UserInfos): The authentication information of the
            current user retrieved from the access token.

    Returns:
        ItemID: A dictionary containing the ID of the created user on success.

    Raises:
        401 Unauthorized: If the user is not authenticated (handled by dependencies).
        403 Forbidden: If the user does not have permission (handled by dependencies).
        409 Conflict: If the user already exists (handled by exception handlers).
        422 Unprocessable Entity: If the input values can't be parsed (handled by
            fastapi).

    """
    user = UserCreate(
        sub=current_user_infos.subject,
        issuer=current_user_infos.issuer,
        name=current_user_infos.user_info["name"],
        email=current_user_infos.user_info["email"],
    )
    msg = f"Creating user with params: {user.model_dump_json()}"
    request.state.logger.info(msg)
    db_user = add_user(session=session, user=user)
    msg = f"User created: {db_user.model_dump_json()}"
    request.state.logger.info(msg)
    return {"id": db_user.id}


@user_router.get(
    "/",
    summary="Retrieve users",
    description="Retrieve a paginated list of users. It is possible to filter and sort "
    "by any field of the entity. It is possible to paginate the returned list.",
)
def retrieve_users(
    request: Request, session: SessionDep, params: UserQueryDep
) -> UserList:
    """Retrieve a paginated list of users based on query parameters.

    Fetches users from the database using pagination, sorting, and additional filters
    provided in the query parameters. Returns the users in a paginated response format.

    Args:
        request (Request): The HTTP request object, used for logging and URL generation.
        session (Session): Database session dependency.
        params (UserQuery): Dependency containing query parameters for filtering,
            sorting, and pagination.

    Returns:
        UserList: A paginated list of users matching the query parameters.

    Raises:
        401 Unauthorized: If the user is not authenticated (handled by dependencies).
        403 Forbidden: If the user does not have permission (handled by dependencies).

    """
    msg = f"Retrieve users. Query params: {params.model_dump_json()}"
    request.state.logger.info(msg)
    users, tot_items = get_users(
        session=session,
        skip=(params.page - 1) * params.size,
        limit=params.size,
        sort=params.sort,
        **params.model_dump(exclude={"page", "size", "sort"}, exclude_none=True),
    )
    msg = f"{tot_items} retrieved users: {[user.model_dump_json() for user in users]}"
    request.state.logger.info(msg)
    return UserList(
        data=users,
        resource_url=str(request.url),
        page_number=params.page,
        page_size=params.size,
        tot_items=tot_items,
    )


@user_router.get(
    "/{user_id}",
    summary="Retrieve user with given ID",
    description="Check if the given user's ID already exists in the DB and return it. "
    "If the user does not exist in the DB, the endpoint raises a 404 error.",
    responses={status.HTTP_404_NOT_FOUND: {"model": ErrorMessage}},
)
def retrieve_user(request: Request, user: UserRequiredDep) -> UserRead:
    """Retrieve a user by their unique identifier.

    Checks if the user exists, and returns the user object if found. If the user does
    not exist, logs an error and returns a JSON response with a 404 status.

    Args:
        request (Request): The incoming HTTP request object.
        user (User): The user object, if found.

    Returns:
        User: The user object if found.

    Raises:
        401 Unauthorized: If the user is not authenticated (handled by dependencies).
        403 Forbidden: If the user does not have permission (handled by dependencies).
        404 Not Found: If the user does not exist (handled by exception handlers).

    """
    msg = f"User with ID '{user.id!s}' found: {user.model_dump_json()}"
    request.state.logger.info(msg)
    return user


@user_router.delete(
    "/{user_id}",
    summary="Delete user with given ID",
    description="Delete a user with the given ID from the DB. If the user has one or "
    "more associated deployments or other entities in the DB, they can't be deleted.",
    status_code=status.HTTP_204_NO_CONTENT,
    responses={
        status.HTTP_400_BAD_REQUEST: {"model": ErrorMessage},
        status.HTTP_409_CONFLICT: {"model": ErrorMessage},
    },
)
def remove_user(
    request: Request,
    session: SessionDep,
    user_id: uuid.UUID | Literal["me"],
    user: UserDep,
) -> None:
    """Remove a user from the system by their unique identifier.

    Logs the deletion process and delegates the actual removal to the `delete_user`
    function. A user can't remove themselves.

    Args:
        request (Request): The HTTP request object, used for logging and request context
        session (Session): The database session dependency.
        user_id (uuid.UUID | Literal["me"]): The unique identifier of the user to be
            removed.
        user (User | None): The DB entity to be removed.

    Returns:
        None

    Raises:
        400 Bad Request: If the user tries to delete themselves (handled below).
        401 Unauthorized: If the user is not authenticated (handled by dependencies).
        403 Forbidden: If the user does not have permission (handled by dependencies).
        409 Conflict: If the user has related entities and can't be deleted (handled by
            dependencies).

    """
    if user_id == "me":
        msg = "User can't delete themselves."
        request.state.logger.info(msg)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=msg)
    msg = f"Delete user with ID '{user_id!s}'"
    request.state.logger.info(msg)
    if user is not None:
        delete_user(session=session, user=user)
    msg = f"User with ID '{user_id!s}' deleted"
    request.state.logger.info(msg)


@user_router.post(
    "/{user_id}/ssh_keys",
    summary="Generate user's private and public key",
    description="Generate a private and public key. Store private key on vault and "
    "update the public ssh key of the user with the given ID. If the any of the keys "
    "have already been inserted, raise a 409 conflic error (they must be deleted). If "
    "the user does not exist raise a 404 error.",
    status_code=status.HTTP_201_CREATED,
    responses={
        status.HTTP_404_NOT_FOUND: {"model": ErrorMessage},
        status.HTTP_409_CONFLICT: {"model": ErrorMessage},
        status.HTTP_422_UNPROCESSABLE_ENTITY: {"model": ErrorMessage},
    },
)
def add_user_ssh_keys(
    request: Request,
    session: SessionDep,
    user: UserRequiredDep,
    credentials: AuthenticationDep,
    settings: SettingsDep,
) -> None:
    """Add a private and public ssh key to an existing user.

    Generate a private and public key. Store private key on vault if enabled.
    Update the public ssh key of the user with the given ID.

    Args:
        request (Request): The current request object.
        session (Session): The database session dependency.
        user (User): The user entity to update, if it exists.
        credentials (UserInfos): User credentials.
        settings (Settings): Application settings.

    Returns:
        None

    Raises:
        401 Unauthorized: If the user is not authenticated (handled by dependencies).
        403 Forbidden: If the user does not have permission (handled by dependencies).
        404 Not Found: If the user does not exist (handled by exception handlers).
        409 Conflict: If the user already has a public key (handled by exception
            handlers).
        422 Unprocessable Entity: If the input data are not valid (handled by fastapi).

    """
    msg = f"Add public key to user with ID '{user.id!s}'"
    request.state.logger.info(msg)
    if user.public_ssh_key is not None:
        msg = f"User with ID '{user.id!s}' already has a public key assigned."
        request.state.logger.error(msg)
        raise ConflictError(msg)

    private_key, public_key = create_ssh_keys()
    if settings.VAULT_ENABLE:
        store_private_key(
            private_key=private_key,
            issuer=credentials.issuer,
            sub=credentials.subject,
            access_token=credentials.access_token_info,
            settings=settings,
            logger=request.state.logger,
        )
    else:
        msg = "Vault connection is not enabled. Private key will not be stored."
        request.state.logger.warning(msg)

    update_user(
        session=session, user=user, new_data=UserUpdate(public_ssh_key=public_key)
    )
    msg = f"Public key added to user with ID '{user.id!s}'"
    request.state.logger.info(msg)


@user_router.patch(
    "/{user_id}/ssh_keys",
    summary="Update user's public key",
    description="Update the public ssh key of the user with the given ID. If the key "
    "has already been inserted raise a 409 conflic error (it must be deleted). If the "
    "user does not exist raise a 404 error.",
    responses={
        status.HTTP_404_NOT_FOUND: {"model": ErrorMessage},
        status.HTTP_409_CONFLICT: {"model": ErrorMessage},
        status.HTTP_422_UNPROCESSABLE_ENTITY: {"model": ErrorMessage},
    },
)
def add_user_public_key(
    request: Request,
    session: SessionDep,
    user: UserRequiredDep,
    public_key: Annotated[
        str,
        Field(description="Public ssh key"),
        AfterValidator(verify_public_ssh_key),
        Body(embed=True),
    ],
) -> None:
    """Add a public ssh key to an existing user.

    Updating a public ssh key does not involve updating Vault.

    Args:
        request (Request): The current request object.
        session (Session): The database session dependency.
        user (User): The user entity to update, if it exists.
        public_key (str): The ssh public key to associate to the user.

    Returns:
        None

    Raises:
        401 Unauthorized: If the user is not authenticated (handled by dependencies).
        403 Forbidden: If the user does not have permission (handled by dependencies).
        404 Not Found: If the user does not exist (handled by exception handlers).
        409 Conflict: If the user already has a public key (handled by exception
            handlers).
        422 Unprocessable Entity: If the input data are not valid (handled by fastapi).

    """
    msg = f"Add public key to user with ID '{user.id!s}'"
    request.state.logger.info(msg)
    if user.public_ssh_key is not None:
        msg = f"User with ID '{user.id!s}' already has a public key assigned."
        request.state.logger.error(msg)
        raise ConflictError(msg)

    update_user(
        session=session, user=user, new_data=UserUpdate(public_ssh_key=public_key)
    )
    msg = f"Public key added to user with ID '{user.id!s}'"
    request.state.logger.info(msg)


@user_router.delete(
    "/{user_id}/ssh_keys",
    summary="Delete user's public and private key",
    description="Unset the public and private ssh keys of the user with the given ID."
    "If the user does not exist raise a 404 error.",
    status_code=status.HTTP_204_NO_CONTENT,
)
def remove_user_public_key(
    request: Request,
    session: SessionDep,
    user: UserRequiredDep,
    credentials: AuthenticationDep,
    settings: SettingsDep,
) -> None:
    """Remove a user public key and private key.

    Remove the private key from vault if enabled.
    Update the public ssh key of the user with the given ID.

    Args:
        request (Request): The current request object.
        session (Session): The database session dependency.
        user (User): The user entity to update, if it exists.
        credentials (UserInfos): User credentials.
        settings (Settings): Application settings.

    Returns:
        None

    Raises:
        401 Unauthorized: If the user is not authenticated (handled by dependencies).
        403 Forbidden: If the user does not have permission (handled by dependencies).
        404 Not Found: If the user does not exist (handled by exception handlers).

    """
    msg = f"Delete public key of user with ID '{user.id!s}'"
    request.state.logger.info(msg)

    if settings.VAULT_ENABLE:
        delete_private_key(
            issuer=credentials.issuer,
            sub=credentials.subject,
            access_token=credentials.access_token_info,
            settings=settings,
            logger=request.state.logger,
        )

    if user.public_ssh_key is not None:
        update_user(
            session=session, user=user, new_data=UserUpdate(public_ssh_key=None)
        )
    msg = f"Public key of user with ID '{user.id!s}' deleted"
    request.state.logger.info(msg)
