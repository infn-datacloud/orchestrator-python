"""Endpoints to manage User details."""

from datetime import datetime
from typing import Annotated

from pydantic import AnyHttpUrl, BaseModel, Field

from orchestrator.common.schemas import ItemID, PaginatedList


class UserCreate(BaseModel):
    """Schema used to define request's body parameters."""

    sub: Annotated[str, Field(description="Issuer's subject associated with this user")]
    name: Annotated[str, Field(description="User name and surname")]
    email: Annotated[str, Field(description="User email address")]
    issuer: Annotated[AnyHttpUrl, Field(description="Issuer URL")]


class UserSingle(UserCreate, ItemID):
    """Schema used to return User's data to clients."""

    created_at: Annotated[
        datetime, Field(description="Date time of when the entity has been created")
    ]


class UserList(PaginatedList):
    """Schema used to return paginated list of Users' data to clients."""

    data: Annotated[
        list[UserSingle], Field(default_factory=list, description="List of users")
    ]
