"""Utility functions."""

from fastapi import APIRouter, Response
from fastapi.routing import APIRoute


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
