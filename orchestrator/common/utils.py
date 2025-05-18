"""Utility functions"""

from typing import Any

from fastapi import APIRouter, Response
from fastapi.datastructures import URL
from fastapi.routing import APIRoute

from orchestrator.common.schemas import PageNavigation, Pagination


def get_page_navigation(
    *, url: URL, size: int, curr_page: int, tot_pages: int
) -> PageNavigation:
    """From the current URL build navigation links.

    Strip current query parameters from the given URL. Detect previous and next page
    from the current one. Knowing the total pages build the last page link."""

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
    """Retrieve a dict with navigation, pagination and data details.

    This dict will be converted to the paginated model returned by a specific endpoint.
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
    """Add the 'Allow' header to the response.

    This header contains the available methods for the specified rosource. Used mainly
    in the OPTIONS method.
    """
    allowed_methods: set[str] = set()
    for route in router.routes:
        if isinstance(route, APIRoute):
            allowed_methods.update(route.methods)
    response.headers["Allow"] = ", ".join(allowed_methods)
    return response
