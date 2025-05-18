"""Common pydantic schemas."""

import math
import uuid
from datetime import datetime
from typing import Annotated

from pydantic import AnyHttpUrl, computed_field
from sqlmodel import Field, SQLModel


class ItemID(SQLModel):
    """Model usually returned by POST operation with only the item ID.

    All DB entities must inherit from this entity.
    """

    id: Annotated[
        uuid.UUID,
        Field(
            default_factory=uuid.uuid4,
            description="Item unique ID in the DB",
            primary_key=True,
        ),
    ]


class ErrorMessage(SQLModel):
    """Model returned when raising an HTTP exception such as 404."""

    title: Annotated[str, Field(description="Error title")]
    message: Annotated[str, Field(description="Error detailed description")]


class CreationQuery(SQLModel):
    """Schema used to define request's body parameters."""

    created_before: Annotated[
        datetime | None,
        Field(
            default=None,
            description="Item's creation time must be lower than or equal to this "
            "value",
        ),
    ]
    created_after: Annotated[
        datetime | None,
        Field(
            default=None,
            description="Item's creation time must be greater than or equal to this "
            "value",
        ),
    ]


class UpdateQuery(SQLModel):
    """Schema used to define request's body parameters."""

    updated_before: Annotated[
        datetime | None,
        Field(
            default=None,
            description="Item's creation time must be lower than or equal to this "
            "value",
        ),
    ]
    updated_after: Annotated[
        datetime | None,
        Field(
            default=None,
            description="Item's creation time must be greater than or equal to this "
            "value",
        ),
    ]


class PaginationQuery(SQLModel):
    """Model to filter lists in GET operations with multiple items."""

    size: Annotated[int, Field(default=5, ge=1, description="Chunk size.")]
    page: Annotated[
        int, Field(default=1, ge=1, description="Divide the list in chunks")
    ]
    sort: Annotated[
        str,
        Field(
            default="-created_at",
            description="Name of the key to use to sort values. "
            "Prefix the '-' char to the chosen key to use reverse order.",
        ),
    ]


class Pagination(SQLModel):
    """With pagination details and total elements count."""

    size: Annotated[int, Field(default=5, ge=1, description="Chunk size.")]
    number: Annotated[
        int, Field(default=1, ge=1, description="Divide the list in chunks")
    ]
    total_elements: Annotated[int, Field(description="Total number of items")]

    @computed_field
    @property
    def total_pages(self) -> int:
        """Return the ceiling value of tot_items/page size.

        If there are no elements, there is still one page but with no items.
        """
        val = math.ceil(self.total_elements / self.size)
        return 1 if val == 0 else val


class PageNavigation(SQLModel):
    """Model with the navigation links to use to navigate through a paginated list."""

    first: Annotated[AnyHttpUrl, Field(description="Link to the first page")]
    prev: Annotated[
        AnyHttpUrl | None, Field(description="Link to the previous page if available")
    ]
    next: Annotated[
        AnyHttpUrl | None, Field(description="Link to the next page if available")
    ]
    last: Annotated[AnyHttpUrl, Field(description="Link to the last page")]


class PaginatedList(SQLModel):
    """Model with the pagination details and navigation links.

    Models with lists returned by GET operations MUST inherit from this model.
    """

    links: Annotated[
        PageNavigation,
        Field(description="Links useful to navigate toward other pages"),
    ]
    page: Annotated[Pagination, Field(description="Page details")]
