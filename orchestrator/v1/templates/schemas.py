"""Templates schemas returned by the endpoints."""

import hashlib
import json
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


def yaml_to_json(value: str) -> str:
    """Verify that TOSCA template is a YAML file and convert to json.

    Args:
        value (str): TOSCA template string.

    Returns:
        str: the JSON formatted template

    Raises:
        ValueError if input is not in YAML format.

    """
    try:
        obj = yaml.safe_load(value)
        txt = json.dumps(obj, indent=2)
        return txt
    except yaml.YAMLError as e:
        raise ValueError("Input TOSCA template is not a valid YAML file") from e


class TemplateBase(SQLModel):
    """Schema with the basic parameters of the Template entity."""

    content: Annotated[
        str,
        Field(description="TOSCA template body. YAML format"),
        AfterValidator(yaml_to_json),
    ]


class TemplateCreate(TemplateBase):
    """Schema used to define request's body parameters of a POST on /templates."""

    @computed_field
    @property
    def hash_content(self) -> str:
        """Calculate hash for TOSCA template content."""
        return hashlib.sha256(self.content.encode()).hexdigest()

    @computed_field
    @property
    def name(self) -> str | None:
        """Retrieve the template name from the content's metadata."""
        data = yaml.safe_load(self.content)
        return data.get("metadata", {}).get("template_name", None)

    @computed_field
    @property
    def version(self) -> str | None:
        """Retrieve the template version from the content's metadata."""
        data = yaml.safe_load(self.content)
        return data.get("metadata", {}).get("template_version", None)

    @computed_field
    @property
    def target_provider_type(self) -> str | None:
        """Retrieve the template target provider type from the content's metadata."""
        data = yaml.safe_load(self.content)
        return data.get("metadata", {}).get("target_provider_type", None)

    @computed_field
    @property
    def tosca_definitions_version(self) -> str | None:
        """Retrieve the TOSCA version from the content's metadata."""
        data = yaml.safe_load(self.content)
        return data.get("tosca_definitions_version", None)


class TemplateUpdate(SQLModel):
    """Schema used to define request's body parameters of a PATCH on /templates."""

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
        list[TemplateRead], Field(default_factory=list, description="List of templates")
    ]


class TemplateQuery(CreationTimeQuery, PaginationQuery, SortQuery, TemplateUpdate):
    """Schema used to define request's parameters for query filtering."""

    content: Annotated[
        str | None,
        Field(
            default=None,
            description="TOSCA template's content must contain this string",
        ),
    ]


TemplateQueryDep = Annotated[TemplateQuery, Query()]
