"""Endpoints to manage User details."""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import AnyHttpUrl, BaseModel, Field

user_router = APIRouter(prefix="/users", tags=["users"])


class User(BaseModel):
    sub: str = Field(description="Issuer's subject associated with this user")
    name: str = Field(description="User name and surname")
    email: str = Field(description="User email address")
    issuer: AnyHttpUrl = Field(description="Issuer URL")


def get_user(user_id: str) -> User | None:
    """Dependency to search a user with the given user_id in the DB."""
    # TODO search in the DB
    return None


@user_router.head(
    "/{user_id}",
    response_model=None,
    summary="Allows the client to check if a user's subject already exists in the DB.",
    status_code=status.HTTP_204_NO_CONTENT,
)
def check_user_existence(user: Annotated[User, Depends(get_user)]):
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User with sub '{user_id}' not found",
        )
