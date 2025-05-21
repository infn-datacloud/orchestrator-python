"""Endpoints to manage User details."""

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, Request, Response, Security, status
from fastapi.responses import JSONResponse

from orchestrator.auth import has_admin_access, has_user_access
from orchestrator.common.exceptions import ConflictError
from orchestrator.common.schemas import ErrorMessage, ItemID
from orchestrator.common.utils import add_allow_header_to_resp, get_paginated_list
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
    add_allow_header_to_resp(user_router, response)


@user_router.post(
    "/",
    responses={status.HTTP_409_CONFLICT: {"model": ErrorMessage}},
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
    return get_paginated_list(
        filtered_items=users,
        tot_items=tot_items,
        url=request.url,
        page=params.page,
        size=params.size,
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
    request.state.logger.info("Delete user with ID '%s'", str(user_id))
    delete_user(session=session, user_id=user_id)
    request.state.logger.info("User with ID '%s' deleted", str(user_id))
