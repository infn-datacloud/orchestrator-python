"""Users schemas returned by the endpoints."""

from typing import Annotated

from fastapi import Query
from pydantic import AnyHttpUrl, EmailStr
from sqlmodel import AutoString, Field, SQLModel

from orchestrator.utils import HttpUrlType
from orchestrator.v1.schemas import (
    CreationTimeQuery,
    CreationTimeRead,
    ItemID,
    PaginatedList,
    PaginationQuery,
    SortQuery,
)


class UserBase(SQLModel):
    """Schema with the basic parameters of the User entity."""

    sub: Annotated[str, Field(description="Subject associated with this user")]
    name: Annotated[str, Field(description="User name and surname")]
    username: Annotated[
        str,
        Field(
            description="User preferred username. To be used when creating home on VMs"
        ),
    ]
    email: Annotated[
        EmailStr, Field(sa_type=AutoString, description="User email address")
    ]
    issuer: Annotated[AnyHttpUrl, Field(sa_type=HttpUrlType, description="Issuer URL")]


class UserCreate(UserBase):
    """Schema used to define request's body parameters of a POST on /users."""


class UserUpdate(SQLModel):
    """Schema used to define request's body parameters of a PATCH on /users."""

    public_ssh_key: Annotated[
        str | None, Field(default=None, description="User's public ssh key")
    ]
    refresh_token: Annotated[
        str | None,
        Field(
            default=None,
            description="User's refresh token, used for long running procedure",
        ),
    ]


class UserRead(ItemID, CreationTimeRead, UserBase, UserUpdate):
    """Schema used to return User's data to clients."""


class UserList(PaginatedList):
    """Schema used to return paginated list of Users' data to clients."""

    data: Annotated[
        list[UserRead], Field(default_factory=list, description="List of users")
    ]


class UserQuery(CreationTimeQuery, PaginationQuery, SortQuery, UserUpdate):
    """Schema used to define request's parameters for query filtering."""

    sub: Annotated[
        str | None,
        Field(default=None, description="User's subject must contain this string"),
    ]
    name: Annotated[
        str | None,
        Field(default=None, description="User's name must contains this string"),
    ]
    email: Annotated[
        str | None,
        Field(
            default=None, description="User's email address must contain this string"
        ),
    ]
    issuer: Annotated[
        str | None,
        Field(default=None, description="User's issuer URL must contain this string"),
    ]


UserQueryDep = Annotated[UserQuery, Query()]
