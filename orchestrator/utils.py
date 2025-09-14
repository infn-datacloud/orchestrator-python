"""Utility functions and adapters for specific pydantic types."""

import re
from datetime import datetime, timezone
from typing import Any

from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from fastapi import APIRouter, Response
from fastapi.routing import APIRoute
from pydantic import AnyHttpUrl
from sqlmodel import String, TypeDecorator

MAX_LEN = 255
KEY_EXP = 65537
KEY_SIZE = 2048


class HttpUrlType(TypeDecorator):
    """SQL Adapter to translate an HttpUrl into a string and vice versa."""

    impl = String(MAX_LEN)
    cache_ok = True
    python_type = AnyHttpUrl

    def process_bind_param(self, value, dialect) -> str:
        """Convert the AnyHttpUrl value to a string before storing in the database.

        Args:
            value: The AnyHttpUrl value to be stored.
            dialect: The database dialect in use.

        Returns:
            str: The string representation of the URL.

        """
        return str(value)

    def process_result_value(self, value, dialect) -> AnyHttpUrl:
        """Convert the string value from the database back to an AnyHttpUrl.

        Args:
            value: The string value retrieved from the database.
            dialect: The database dialect in use.

        Returns:
            AnyHttpUrl: The reconstructed AnyHttpUrl object.

        """
        return AnyHttpUrl(url=value)

    def process_literal_param(self, value, dialect) -> str:
        """Convert the AnyHttpUrl value to a string for literal SQL statements.

        Args:
            value: The AnyHttpUrl value to be used in a literal SQL statement.
            dialect: The database dialect in use.

        Returns:
            str: The string representation of the URL.

        """
        return str(value)


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


def split_camel_case(text: str) -> str:
    """Split a camel case string into words separated by spaces.

    Args:
        text: The camel case string to split.

    Returns:
        str: The string with spaces inserted between camel case words.

    """
    matches = re.finditer(
        r".+(?:(?<=[a-z0-9])(?=[A-Z])|(?<=[A-Z0-9])(?=[A-Z][a-z])|$)", text
    )
    return " ".join([m.group(0) for m in matches])


def check_list_not_empty(items: list[Any]) -> list[Any]:
    """Check if the input is a non-empty list, raising ValueError if empty.

    If the argument is a list and it is empty, raises a ValueError.

    Args:
        items (list[Any]): The input to check. Can be a list of any type or a single
            item.

    Returns:
        list[Any]: The original input if it is not an empty list.

    Raises:
        ValueError: If the input is a list and it is empty.

    """
    if isinstance(items, list) and len(items) <= 0:
        raise ValueError("List must not be empty")
    return items


def isoformat(d: datetime) -> str:
    """Convert a datetime or date object to an ISO 8601 format.

    UTC with millisecond precision.

    Args:
        d (datetime): The datetime or date object to format.

    Returns:
        str: The ISO 8601 formatted string representation of the input.

    Raises:
        AttributeError: If the input object does not have an 'astimezone' method.

    """
    try:
        return d.astimezone(timezone.utc).isoformat(timespec="milliseconds")
    except AttributeError as e:
        raise ValueError(
            f"Input value is not a datetime instance. Type: {type(d)}"
        ) from e


def create_ssh_keys() -> tuple[str, str]:
    """Generate ssh keys couples.

    Retuns:
        (str, str): private and public ssh keys couple.

    """
    key = rsa.generate_private_key(
        backend=default_backend(), public_exponent=KEY_EXP, key_size=KEY_SIZE
    )
    private_key = key.private_bytes(
        serialization.Encoding.PEM,
        serialization.PrivateFormat.PKCS8,
        serialization.NoEncryption(),
    )
    public_key = key.public_key().public_bytes(
        serialization.Encoding.OpenSSH, serialization.PublicFormat.OpenSSH
    )

    return private_key.decode("utf-8"), public_key.decode("utf-8")


def verify_public_ssh_key(key: str) -> bool:
    """Verify that the key is a public ssh key.

    Args:
        key (str): public ssh key to validate.

    Returns:
        bool: True if a valid public ssh key, false otherwise.

    """
    try:
        serialization.load_ssh_public_key(key, backend=default_backend())
        return key
    except ValueError as e:
        raise ValueError("Input value is not a valid SSH public key") from e
