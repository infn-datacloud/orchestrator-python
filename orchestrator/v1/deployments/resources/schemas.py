"""Resources schemas returned by the endpoints."""

import uuid
from enum import Enum
from typing import Annotated, Any

from fastapi import Query
from pydantic import computed_field
from sqlmodel import JSON, Column, Field, SQLModel

from orchestrator.v1.schemas import (
    CreationQuery,
    CreationRead,
    EditableRead,
    ItemID,
    PaginatedList,
    PaginationQuery,
    SortQuery,
)


class ResourceStatus(int, Enum):
    """States for a deployment procedure."""

    CONFIGURED = 0
    CONFIGURING = 1
    CREATED = 2
    CREATING = 3
    DELETED = 4
    DELETING = 5
    ERROR = 6
    INITIAL = 7
    STARTED = 8
    STARTING = 9
    STOPPED = 10
    STOPPING = 11


class ResourceBase(SQLModel):
    """Schema with the basic parameters of the Resource entity."""

    im_vm_idx: Annotated[
        int | None,
        Field(
            description="The index of the VM created by the IM. Corresponds to the "
            "im_id field in the data.vms_list of the deployment corresponding "
            "infrastructure entry in the IM DB. It is not None only for Compute TOSCA "
            "node types. Can be None if the resource has not been assigned yet or a "
            "corresponding item does not exist in the IM DB (for example Network, "
            "Port...)"
        ),
    ]
    status: Annotated[
        ResourceStatus,
        Field(
            default=ResourceStatus.INITIAL,
            description="Dictionary with the TOSCA template inputs",
        ),
    ]
    tosca_node_name: Annotated[
        str, Field(description="The name of the represented TOSCA node")
    ]
    tosca_node_type: Annotated[
        str, Field(description="The type of the represented TOSCA node")
    ]
    info: Annotated[
        dict[str, Any] | None,
        Field(
            default=None,
            sa_column=Column(JSON),
            description="Additional information. They are the content field info of "
            "the corresponding item in the data.vms_list field. It is None for entries "
            "not linked to an infrastructure or infrastructures not yet configured. "
            "They are also the source for the template output generation.",
        ),
    ]


class ResourceCreate(ResourceBase):
    """Schema used to create resources."""


class ResourceRead(ItemID, CreationRead, EditableRead, ResourceBase):
    """Schema used to return Resource's data to clients."""

    required_by: Annotated[
        list[uuid.UUID], Field(description="List or nodes requiring this node.")
    ]

    @computed_field
    @property
    def status_name(self) -> str:
        """Status name for human readability."""
        return self.status.name


class ResourceList(PaginatedList):
    """Schema used to return paginated list of Resources' data to clients."""

    data: Annotated[
        list[ResourceRead],
        Field(default_factory=list, description="List of deployments"),
    ]


class ResourceQuery(CreationQuery, PaginationQuery, SortQuery):
    """Schema used to define request's body parameters."""


ResourceQueryDep = Annotated[ResourceQuery, Query()]
