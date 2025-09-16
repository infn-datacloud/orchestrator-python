"""Deployments schemas returned by the endpoints."""

import urllib.parse
import uuid
from enum import Enum
from typing import Annotated, Any

from fastapi import Query
from pydantic import AnyHttpUrl, computed_field
from sqlmodel import JSON, AutoString, Column, Field, SQLModel

from orchestrator.utils import HttpUrlType
from orchestrator.v1 import LOGS_PREFIX, RESOURCES_PREFIX, TEMPLATES_PREFIX
from orchestrator.v1.schemas import (
    CreationQuery,
    CreationRead,
    EditableRead,
    ItemID,
    PaginatedList,
    PaginationQuery,
    SortQuery,
)


class DeploymentStatus(int, Enum):
    """States for a deployment procedure."""

    CREATE_COMPLETE = 0
    CREATE_FAILED = 1
    CREATE_IN_PROGRESS = 2
    DELETE_COMPLETE = 3
    DELETE_FAILED = 4
    DELETE_IN_PROGRESS = 5
    UNKNOWN = 6
    UPDATE_COMPLETE = 7
    UPDATE_FAILED = 8
    UPDATE_IN_PROGRESS = 9


class DeploymentTask(int, Enum):
    """States for a deployment procedure."""

    # On successful DB creation and before sending it to template parser
    template_validation = 0

    # After template validation and before sending to provider selector
    provider_filtering = 1

    # After provider filtering and before sending to ai ranker
    providers_ranking = 2

    # After provider ranking and before sending to IM.
    infrastructure_creation = 3

    # After IM completes (Infrastructure created)
    resources_generated = 4

    # After update request and before sending to IM,
    resources_updating = 5


class DeploymentBase(SQLModel):
    """Schema with the basic parameters of the Deployment entity."""

    template_id: Annotated[
        uuid.UUID,
        Field(description="ID of the matching template", foreign_key="template.id"),
    ]
    template_inputs: Annotated[
        dict[str, Any],
        Field(
            sa_column=Column(JSON),
            description="Dictionary with the TOSCA template inputs",
        ),
    ]
    user_group: Annotated[
        str,
        Field(description="User group owning the resources used for this deployment"),
    ]
    per_provider_max_retries: Annotated[
        int,
        Field(
            default=3,
            ge=1,
            le=10,
            description="Maximum number of retries for each provider. In range [1,10].",
        ),
    ]
    max_providers: Annotated[
        int | None,
        Field(
            default=None,
            ge=1,
            description="The maximum number of cloud providers on which attempt to "
            "create the deployment. In range [1, +inf)",
        ),
    ]
    timeout: Annotated[
        int,
        Field(
            default=14400,
            ge=1,
            le=14400,
            description="Overall timeout value in minutes. It must be greater than 0. "
            "In range [1,14400]",
        ),
    ]
    per_provider_timeout: Annotated[
        int,
        Field(
            default=1440,
            ge=1,
            le=1440,
            description="Timeout value for a single provider (it does not apply to "
            "single tries but it is the overall timeout for a provider). If provided, "
            "it must be greater than 0 and equal or lower than tot_timeout_mins",
        ),
    ]
    keep_last_attempt: Annotated[
        bool,
        Field(
            default=False,
            description="Whether the IM, in case of failure, will keep the resources "
            "of the last attempted deployment or not.",
        ),
    ]
    target_provider_name: Annotated[
        str | None,
        Field(default=None, description="Name of the target provider to use"),
    ]
    target_region_name: Annotated[
        str | None, Field(default=None, description="Name of the target region to use")
    ]


class DeploymentInternal(SQLModel):
    """Schema with the attributes which can't be used when creating an instnce."""

    user_group_issuer: Annotated[
        AnyHttpUrl, Field(sa_type=HttpUrlType, description="User group's issuer")
    ]
    status: Annotated[
        DeploymentStatus,
        Field(
            default=DeploymentStatus.CREATE_IN_PROGRESS, description="Deployment status"
        ),
    ]
    template_outputs: Annotated[
        dict[str, Any] | None,
        Field(
            default=None,
            sa_column=Column(JSON),
            description="Dictionary with the TOSCA template otuputs",
        ),
    ]
    target_iaas_project: Annotated[
        str | None,
        Field(
            default=None,
            description="IaaS tenant/namespace chosen by the orchestrator.",
        ),
    ]
    im_infrastructure_id: Annotated[
        str | None,
        Field(
            default=None,
            description="ID of the corresponding infrastructure in the IM DB.",
        ),
    ]
    status_reason: Annotated[
        str | None,
        Field(
            default=None,
            description="Verbose explanation of reason that led to the deployment "
            "status. It is not None only if the deployment is in an erroneous status.",
        ),
    ]
    task: Annotated[
        DeploymentTask,
        Field(
            default=DeploymentTask.template_validation, description="Deployment status"
        ),
    ]


class DeploymentCreate(DeploymentBase):
    """Schema used to define request's body parameters of a POST on /deployments."""


class DeploymentUpdate(SQLModel):
    """Schema used to define request's body parameters of a PATCH on /deployments."""

    user_group: Annotated[
        str | None,
        Field(
            default=None,
            description="User group owning the resources used for this deployment",
        ),
    ]


class DeploymentLinks(SQLModel):
    """Schema used to return Deployment's related entities to clients."""

    templates: Annotated[
        AnyHttpUrl,
        Field(description="Link to retrieve the template linked to this deployment."),
    ]
    resources: Annotated[
        AnyHttpUrl,
        Field(
            description="Link to retrieve the resources belonging to this deployment."
        ),
    ]
    logs: Annotated[
        AnyHttpUrl,
        Field(description="Link to retrieve the logs belonging to this deployment."),
    ]


class DeploymentRead(
    ItemID, CreationRead, EditableRead, DeploymentBase, DeploymentInternal
):
    """Schema used to return Deployment's data to clients."""

    owned_by: Annotated[
        list[uuid.UUID],
        Field(
            sa_type=AutoString,
            description="List of the provider/site administrator IDs",
        ),
    ]

    base_url: Annotated[
        AnyHttpUrl, Field(exclude=True, description="Base URL for the children URL")
    ]

    @computed_field
    @property
    def links(self) -> DeploymentLinks:
        """Build the templates endpoints in the DeploymentLinks object.

        Returns:
            DeploymentLinks: An object with the deployment's useful links.

        """
        templates_link = urllib.parse.urljoin(
            str(self.base_url), f"{self.id}{TEMPLATES_PREFIX}"
        )
        resources_link = urllib.parse.urljoin(
            str(self.base_url), f"{self.id}{RESOURCES_PREFIX}"
        )
        logs_link = urllib.parse.urljoin(str(self.base_url), f"{self.id}{LOGS_PREFIX}")
        return DeploymentLinks(
            templates=templates_link, resources=resources_link, logs=logs_link
        )

    @computed_field
    @property
    def status_name(self) -> str:
        """Status name for human readability."""
        return self.status.name

    @computed_field
    @property
    def task_name(self) -> str:
        """Task name for human readability."""
        return self.task.name


class DeploymentList(PaginatedList):
    """Schema used to return paginated list of Deployments' data to clients."""

    data: Annotated[
        list[DeploymentRead],
        Field(default_factory=list, description="List of deployments"),
    ]


class DeploymentQuery(CreationQuery, PaginationQuery, SortQuery):
    """Schema used to define request's body parameters."""

    user_group: Annotated[
        str | None,
        Field(
            default=None, description="Deployment's user group must contain this string"
        ),
    ]
    user_group_issuer: Annotated[
        str | None,
        Field(default=None, description="User group's issuer must contain this string"),
    ]
    template_id: Annotated[
        uuid.UUID,
        Field(description="The matching template ID must be equal to this value"),
    ]
    per_provider_max_retries_gte: Annotated[
        int | None,
        Field(
            default=None,
            description="Max retries for each provider must be greater than or equal",
        ),
    ]
    per_provider_max_retries_lte: Annotated[
        int | None,
        Field(
            default=None,
            description="Max retries for each provider must be lower than or equal",
        ),
    ]
    max_providers_gte: Annotated[
        int | None,
        Field(
            default=None,
            description="Max cloud providers on which attempt creation must be "
            "greater than or equal",
        ),
    ]
    max_providers_lte: Annotated[
        int | None,
        Field(
            default=None,
            description="Max cloud providers on which attempt creation must be "
            "lower than or equal",
        ),
    ]
    timeout_gte: Annotated[
        int | None,
        Field(
            default=None, description="Overall timeout must be greater than or equal"
        ),
    ]
    timeout_lte: Annotated[
        int | None,
        Field(default=None, description="Overall timeout must be lower than or equal"),
    ]
    per_provider_timeout_gte: Annotated[
        int | None,
        Field(
            default=None,
            description="Timeout for single provider must be greater than or equal",
        ),
    ]
    per_provider_timeout_lte: Annotated[
        int | None,
        Field(
            default=None,
            description="Timeout for single provider must lower than or equal",
        ),
    ]
    keep_last_attempt: Annotated[
        bool | None,
        Field(default=None, description="Filter deployments with matching flag"),
    ]
    target_provider_name: Annotated[
        str | None,
        Field(
            default=None,
            description="Deployment's target provider must contain this string",
        ),
    ]
    target_region_name: Annotated[
        str | None,
        Field(
            default=None,
            description="Deployment's target region must contain this string",
        ),
    ]
    target_iaas_project: Annotated[
        str | None,
        Field(
            default=None,
            description="IaaS tenant/namespace chosen by the orchestrator must contain "
            "this string.",
        ),
    ]
    im_infrastructure_id: Annotated[
        str | None,
        Field(
            default=None,
            description="ID of the corresponding infrastructure in the IM DB must "
            "contain this string.",
        ),
    ]
    status_reason: Annotated[
        str | None,
        Field(default=None, description="Status reason must contain this string."),
    ]
    status: Annotated[
        list[DeploymentStatus],
        Field(
            default_factory=list,
            description="Deployment status must be one of the specified ones. "
            "If not specified no filtering is applied",
        ),
    ]
    task: Annotated[
        list[DeploymentTask],
        Field(default_factory=list, description="Deployment status"),
    ]


DeploymentQueryDep = Annotated[DeploymentQuery, Query()]
