"""Common SQLAlchemy adapter for specific pydantic types."""

from pydantic import AnyHttpUrl
from sqlmodel import String, TypeDecorator

MAX_LEN = 255


class HttpUrlType(TypeDecorator):
    """SQL Adapter to translate an HttpUrl into a string and vice versa."""

    impl = String(MAX_LEN)
    cache_ok = True
    python_type = AnyHttpUrl

    def process_bind_param(self, value, dialect) -> str:
        return str(value)

    def process_result_value(self, value, dialect) -> AnyHttpUrl:
        return AnyHttpUrl(url=value)

    def process_literal_param(self, value, dialect) -> str:
        return str(value)
