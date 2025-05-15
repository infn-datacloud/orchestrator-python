"""Module with the configuration parameters."""

from enum import Enum
from typing import Annotated

from pydantic import AnyHttpUrl, EmailStr, Field
from pydantic_settings import BaseSettings, SettingsConfigDict

API_V1_STR = "/api/v1/"


class AuthorizationMethodsEnum(str, Enum):
    email = "email"
    opa = "opa"


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

    model_config = SettingsConfigDict(env_file=".env")

    # ROOT_PATH: str | None = None

    # ADMIN_EMAIL_LIST: list[EmailStr] = []

    # DOC_V1_URL: Optional[AnyHttpUrl] = None

    # @validator("DOC_V1_URL", pre=True)
    # @classmethod
    # def create_doc_url(cls, v: Optional[str], values: dict[str, Any]) -> str:
    #     """Build URL for internal documentation."""
    #     if v:
    #         return v
    #     protocol = "http"
    #     root_path = values.get("ROOT_PATH", "/")
    #     root_path = root_path[1:] if root_path is not None else ""
    #     link = os.path.join(
    #         values.get("DOMAIN"), root_path, values.get("API_V1_STR")[1:], "docs"
    #     )
    #     return f"{protocol}://{link}"

    # # BACKEND_CORS_ORIGINS is a JSON-formatted list of origins
    # # e.g: '["http://localhost", "http://localhost:4200",
    # # "http://localhost:3000", "http://localhost:8080",
    # # "http://local.dockertoolbox.tiangolo.com"]'
    # # BACKEND_CORS_ORIGINS: list[AnyHttpUrl] = ["http://localhost:3000"]
