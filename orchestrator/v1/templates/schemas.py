"""Templates schemas returned by the endpoints."""

import hashlib
from typing import Annotated

import yaml
from fastapi import Query
from pydantic import AfterValidator, computed_field
from sqlmodel import Field, SQLModel

from orchestrator.v1.schemas import (
    CreationTimeQuery,
    CreationTimeRead,
    ItemID,
    PaginatedList,
    PaginationQuery,
    SortQuery,
)


def tosca_is_yaml(value: str) -> str:
    """Verify that TOSCA template is a YAML file.

    Returns:
        str: the input value

    Raises:
        ValueError if input is not in YAML format.

    """
    try:
        yaml.safe_load(value)
        return value
    except yaml.YAMLError as e:
        raise ValueError("Input TOSCA template is not a valid YAML file") from e


class TemplateBase(SQLModel):
    """Schema with the basic parameters of the Template entity."""

    content: Annotated[
        str,
        Field(description="TOSCA template body. YAML format"),
        AfterValidator(tosca_is_yaml),
    ]


class TemplateCreate(TemplateBase):
    """Schema used to define request's body parameters of a POST on 'users' endpoint."""

    @computed_field
    @property
    def hash_content(self) -> str:
        """Calculate hash for TOSCA template content."""
        return hashlib.sha256(self.content.encode()).hexdigest()

    @computed_field
    @property
    def name(self) -> str | None:
        """Calculate hash for TOSCA template content."""
        data = yaml.safe_load(self.content)
        return data.get("metadata", {}).get("template_name", None)

    @computed_field
    @property
    def version(self) -> str | None:
        """Calculate hash for TOSCA template content."""
        data = yaml.safe_load(self.content)
        return data.get("metadata", {}).get("template_version", None)

    @computed_field
    @property
    def target_provider_type(self) -> str | None:
        """Calculate hash for TOSCA template content."""
        data = yaml.safe_load(self.content)
        return data.get("metadata", {}).get("target_provider_type", None)

    @computed_field
    @property
    def tosca_definitions_version(self) -> str | None:
        """Calculate hash for TOSCA template content."""
        data = yaml.safe_load(self.content)
        return data.get("tosca_definitions_version", None)


class TemplateUpdate(SQLModel):
    """Schema used to define request's body parameters of a PATCH on a specific user."""

    name: Annotated[
        str | None, Field(default=None, description="TOSCA template's name")
    ]
    version: Annotated[
        str | None, Field(default=None, description="TOSCA template's version")
    ]
    target_provider_type: Annotated[
        str | None, Field(default=None, description="Target provider's type")
    ]
    tosca_definitions_version: Annotated[
        str | None, Field(default=None, description="TOSCA language version")
    ]


class TemplateRead(ItemID, CreationTimeRead, TemplateBase, TemplateUpdate):
    """Schema used to return Template's data to clients."""


class TemplateList(PaginatedList):
    """Schema used to return paginated list of Templates' data to clients."""

    data: Annotated[
        list[TemplateRead], Field(default_factory=list, description="List of users")
    ]


class TemplateQuery(CreationTimeQuery, PaginationQuery, SortQuery, TemplateUpdate):
    """Schema used to define request's body parameters."""

    content: Annotated[
        str | None,
        Field(
            default=None,
            description="TOSCA template's content must contain this string",
        ),
    ]


TemplateQueryDep = Annotated[TemplateQuery, Query()]
