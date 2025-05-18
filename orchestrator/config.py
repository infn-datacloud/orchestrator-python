"""Module with the configuration parameters."""

import logging
from enum import Enum
from functools import lru_cache
from typing import Annotated, Literal

from pydantic import AnyHttpUrl, BeforeValidator, EmailStr, Field
from pydantic_settings import BaseSettings, SettingsConfigDict

API_V1_STR = "/api/v1/"


class AuthorizationMethodsEnum(str, Enum):
    email = "email"
    opa = "opa"


class LogLevel(int, Enum):
    DEBUG = logging.DEBUG
    INFO = logging.INFO
    WARNING = logging.WARNING
    ERROR = logging.ERROR
    CRITICAL = logging.CRITICAL


def get_level(value: str) -> int:
    return LogLevel.__getitem__(value.upper())


class Settings(BaseSettings):
    """Model with the app settings."""

    PROJECT_NAME: Annotated[
        str,
        Field(
            default="Orchestrator",
            description="Project name to show in the Swagger documentation",
        ),
    ]
    MAINTAINER_NAME: Annotated[
        str | None, Field(default=None, description="Maintainer name")
    ]
    MAINTAINER_URL: Annotated[
        AnyHttpUrl | None, Field(default=None, description="Maintainer's profile URL")
    ]
    MAINTAINER_EMAIL: Annotated[
        EmailStr | None, Field(default=None, description="Maintainer's email address")
    ]
    BASE_URL: Annotated[
        AnyHttpUrl,
        Field(
            default="http://localhost:8000",
            description="Application base URL. "
            "Used to build documentation redirect links.",
        ),
    ]
    DB_URL: Annotated[
        str,
        Field(
            default="sqlite+pysqlite:///:memory:",
            description="DB URL. By default it use an in memory MySQL DB.",
        ),
    ]
    DB_ECO: Annotated[
        bool, Field(default=False, description="Eco messages exchanged with the DB")
    ]
    LOG_LEVEL: Annotated[
        LogLevel,
        Field(default=LogLevel.INFO, description="Logs level"),
        BeforeValidator(get_level),
    ]
    TRUSTED_IDP_LIST: Annotated[
        list[AnyHttpUrl],
        Field(
            default_factory=list,
            description="List of the application trusted identity providers",
        ),
    ]
    AUTHZ_MODE: Annotated[
        AuthorizationMethodsEnum,
        Field(
            default=AuthorizationMethodsEnum.email,
            description="Authorization method to use. Allowed values: email, opa",
        ),
    ]
    ADMIN_EMAIL_LIST: Annotated[
        list[EmailStr],
        Field(
            default_factory=list,
            description="List of administrator's emails. "
            "To use when AUTHZ_MODE is 'email'",
        ),
    ]
    BACKEND_CORS_ORIGINS: Annotated[
        list[AnyHttpUrl | Literal["*"]],
        Field(
            default=["http://localhost:3000/"],
            description="JSON-formatted list of allowed origins",
        ),
    ]
    KAFKA_SERVERS: Annotated[
        str,
        Field(
            default="localhost:9092",
            description="Comma separated list of Kafka servers",
        ),
    ]
    KAFKA_NEW_DEP_TOPIC: Annotated[
        str,
        Field(
            default="new_deployment_request",
            description="Name of the topic storing new deployment requests",
        ),
    ]

    model_config = SettingsConfigDict(env_file=".env")


@lru_cache
def get_settings() -> Settings:
    """Retrieve cached settings."""
    return Settings()
