"""Endpoints to manage User details."""

from typing import Annotated

from fastapi import APIRouter, Depends, Query, Request, status
from fastapi.responses import JSONResponse

from orchestrator.common.exceptions import ConflictError
from orchestrator.common.schemas import ErrorMessage, ItemID, PaginationQuery
from orchestrator.common.utils import get_paginated_list
from orchestrator.v1.users.dependencies import (
    add_user,
    delete_user,
    get_user,
    get_users,
)
from orchestrator.v1.users.schemas import UserCreate, UserList, UserSingle

user_router = APIRouter(prefix="/users", tags=["users"])


@user_router.post(
    "/",
    responses={status.HTTP_409_CONFLICT: {"model": ErrorMessage}},
    summary="Create a new user",
    description="Add a new user to the DB. Check if a user's subject, for this issuer, "
    "already exists in the DB. If the sub already exists, the endpoint raises a 409 "
    "error.",
    status_code=status.HTTP_201_CREATED,
)
def create_user(user: UserCreate) -> ItemID:
    try:
        id = add_user(user)
        return id
    except ConflictError as e:
        return JSONResponse(
            status_code=status.HTTP_409_CONFLICT,
            content={"title": "User already exists", "message": e.message},
        )


@user_router.get(
    "/", summary="Retrieve users", description="Retrieve a paginated list of users."
)
def retrieve_users(
    request: Request, pagination: Annotated[PaginationQuery, Query()]
) -> UserList:
    users, tot_items = get_users(
        skip=pagination.page * pagination.size,
        limit=pagination.size,
        sort=pagination.sort,
    )
    return get_paginated_list(
        filtered_items=users,
        tot_items=tot_items,
        url=request.url,
        pagination=pagination,
    )


@user_router.head(
    "/{user_id}",
    responses={status.HTTP_404_NOT_FOUND: {"model": None}},
    summary="Check user'sub exists",
    description="Check if a user's subject, for this issuer, already exists in the DB",
)
def check_user_existence(user: Annotated[UserSingle | str, Depends(get_user)]) -> None:
    pass


@user_router.get(
    "/{user_id}",
    responses={status.HTTP_404_NOT_FOUND: {"model": ErrorMessage}},
    summary="Retrieve user with given sub",
    description="Check if a user's subject, for this issuer, already exists in the DB "
    "and return it. If the user does not exist in the DB, the endpoint raises a 404 "
    "error.",
)
def retrieve_user(
    user_id: str, user: Annotated[UserSingle | None, Depends(get_user)]
) -> UserSingle:
    if user is None:
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content={
                "title": "User not found",
                "message": f"User with sub '{user_id}' does not exist",
            },
        )
    return user


@user_router.delete(
    "/{user_id}",
    summary="Delete user with given sub",
    description="Delete a user with the given subject, for this issuer, from the DB.",
    status_code=status.HTTP_204_NO_CONTENT,
)
def remove_user(user_id: str) -> None:
    delete_user(user_id)
