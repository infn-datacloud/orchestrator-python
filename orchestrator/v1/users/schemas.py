"""Users schemas returned by the endpoints."""

from datetime import datetime
from typing import Annotated

from fastapi import Query
from pydantic import AnyHttpUrl, EmailStr
from sqlmodel import AutoString, Field, SQLModel, UniqueConstraint, func

from orchestrator.common.schemas import (
    HttpUrlType,
    ItemID,
    PaginatedList,
    PaginationQuery,
)


class UserCreate(SQLModel):
    """Schema used to define request's body parameters."""

    sub: Annotated[str, Field(description="Issuer's subject associated with this user")]
    name: Annotated[str, Field(description="User name and surname")]
    email: Annotated[
        EmailStr, Field(description="User email address", sa_type=AutoString)
    ]
    issuer: Annotated[AnyHttpUrl, Field(description="Issuer URL", sa_type=HttpUrlType)]


class User(ItemID, UserCreate, table=True):
    """Schema used to return User's data to clients."""

    created_at: Annotated[
        datetime,
        Field(
            description="Date time of when the entity has been created",
            default=func.now(),
        ),
    ]

    __table_args__ = (
        UniqueConstraint("sub", "issuer", name="unique_sub_issuer_couple"),
    )


class UserQuery(PaginationQuery):
    """Schema used to define request's body parameters."""

    sub: Annotated[
        str | None,
        Field(default=None, description="Issuer's subject associated with this user"),
    ]
    name: Annotated[
        str | None, Field(default=None, description="User name and surname")
    ]
    email: Annotated[
        EmailStr | None,
        Field(default=None, description="User email address", sa_type=AutoString),
    ]
    issuer: Annotated[
        AnyHttpUrl | None,
        Field(default=None, description="Issuer URL", sa_type=HttpUrlType),
    ]


class UserList(PaginatedList):
    """Schema used to return paginated list of Users' data to clients."""

    data: Annotated[
        list[User], Field(default_factory=list, description="List of users")
    ]


UserQueryDep = Annotated[UserQuery, Query()]
