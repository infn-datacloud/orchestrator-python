"""Utility functions."""

from typing import Any

from fastapi import APIRouter, Response
from fastapi.datastructures import URL
from fastapi.routing import APIRoute

from orchestrator.common.schemas import PageNavigation, Pagination


def get_page_navigation(
    *, url: URL, size: int, curr_page: int, tot_pages: int
) -> PageNavigation:
    """Build navigation links for paginated API responses.

    Args:
        url: The base URL for navigation links.
        size: The number of items per page.
        curr_page: The current page number.
        tot_pages: The total number of pages available.

    Returns:
        PageNavigation: An object containing first, previous, next, and last page links.

    """
    first_page = url.include_query_params(page=1, size=size)._url
    if curr_page > 1:
        prev_page = url.include_query_params(page=curr_page - 1, size=size)._url
    else:
        prev_page = None

    if curr_page < tot_pages:
        next_page = url.include_query_params(page=curr_page + 1, size=size)._url
    else:
        next_page = None
    last_page = url.include_query_params(page=tot_pages, size=size)._url

    return PageNavigation(
        first=first_page, prev=prev_page, next=next_page, last=last_page
    )


def get_paginated_list(
    *, filtered_items: list[Any], tot_items: int, url: URL, page: int, size: int
) -> dict[str, Any]:
    """Return a dictionary with navigation links, pagination info and the filtered data.

    Args:
        filtered_items: The list of items for the current page.
        tot_items: The total number of items matching the query.
        url: The base URL for navigation links.
        page: The current page number.
        size: The number of items per page.

    Returns:
        dict: A dictionary with 'links', 'page', and 'data' keys for the paginated
        response.

    """
    pagination = Pagination(number=page, size=size, total_elements=tot_items)
    url = url.replace(query="")
    navigation = get_page_navigation(
        url=url,
        size=pagination.size,
        curr_page=pagination.number,
        tot_pages=pagination.total_pages,
    )
    return {"links": navigation, "page": pagination, "data": filtered_items}


def add_allow_header_to_resp(router: APIRouter, response: Response) -> Response:
    """List in the 'Allow' header the available HTTP methods for the resource.

    Args:
        router: The APIRouter instance containing route definitions.
        response: The FastAPI Response object to modify.

    Returns:
        Response: The response object with the 'Allow' header set.

    """
    allowed_methods: set[str] = set()
    for route in router.routes:
        if isinstance(route, APIRoute):
            allowed_methods.update(route.methods)
    response.headers["Allow"] = ", ".join(allowed_methods)
    return response
