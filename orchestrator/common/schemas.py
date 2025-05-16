"""Common pydantic schemas."""

import math
from typing import Annotated

from pydantic import AnyHttpUrl, BaseModel, Field, computed_field


class ErrorMessage(BaseModel):
    """Model returned when raising an HTTP exception such as 404."""

    title: Annotated[str, Field(description="Error title")]
    message: Annotated[str, Field(description="Error detailed description")]


class ItemID(BaseModel):
    """Model usually returned by POST operation with only the item ID."""

    id: Annotated[str, Field(description="Item unique ID in the DB")]


class PaginationQuery(BaseModel):
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


class PaginationResponse(BaseModel):
    """With pagination details and total elements count."""

    size: Annotated[int, Field(default=5, ge=1, description="Chunk size.")]
    number: Annotated[
        int, Field(default=1, ge=1, description="Divide the list in chunks")
    ]
    total_elements: Annotated[int, Field(description="Total number of items")]

    @computed_field
    @property
    def total_pages(self) -> int:
        return math.ceil(self.total_elements / self.size)


class PageNavigation(BaseModel):
    """Model with the navigation links to use to navigate through a paginated list."""

    first: Annotated[AnyHttpUrl, Field(description="Link to the first page")]
    prev: Annotated[
        AnyHttpUrl | None, Field(description="Link to the previous page if available")
    ]
    next: Annotated[
        AnyHttpUrl | None, Field(description="Link to the next page if available")
    ]
    last: Annotated[AnyHttpUrl, Field(description="Link to the last page")]


class PaginatedList(BaseModel):
    """Model with the pagination details and navigation links."""

    links: Annotated[
        PageNavigation,
        Field(description="Links useful to navigate toward other pages"),
    ]
    page: Annotated[PaginationResponse, Field(description="Page details")]
