"""Deployments schemas returned by the endpoints."""

from typing import Annotated

from fastapi import Query
from sqlmodel import Field, SQLModel

from orchestrator.v1.schemas import (
    CreationQuery,
    CreationRead,
    EditableRead,
    ItemID,
    PaginatedList,
    PaginationQuery,
    SortQuery,
)


class DeploymentBase(SQLModel):
    """Schema with the basic parameters of the Deployment entity."""

    # template_inputs: Annotated[
    #     dict[str, Any], Field(description="Dictionary with the TOSCA template inputs")
    # ]
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
    max_provider: Annotated[
        int | None,
        Field(
            default=None,
            ge=1,
            description="The maximum number of cloud providers on which attempt to "
            "create the deployment. In range [1, +inf)",
        ),
    ]
    total_timeout: Annotated[
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
    target_provider: Annotated[
        str | None,
        Field(default=None, description="Name of the target provider to use"),
    ]
    target_region: Annotated[
        str | None, Field(default=None, description="Name of the target region to use")
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


class DeploymentRead(ItemID, CreationRead, EditableRead, DeploymentBase):
    """Schema used to return Deployment's data to clients."""


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
    # per_provider_max_retries: Annotated[
    #     int,
    #     Field(
    #         default=3,
    #         ge=1,
    #         le=10,
    #         description="Max number of retries for each provider. In range [1,10]",
    #     ),
    # ]
    # max_provider: Annotated[
    #     int | None,
    #     Field(
    #         default=None,
    #         ge=1,
    #         description="The maximum number of cloud providers on which attempt to "
    #         "create the deployment. In range [1, +inf)",
    #     ),
    # ]
    # total_timeout: Annotated[
    #     int,
    #     Field(
    #         default=14400,
    #         ge=1,
    #         le=14400,
    #        description="Overall timeout value in minutes. It must be greater than 0. "
    #         "In range [1,14400]",
    #     ),
    # ]
    # per_provider_timeout: Annotated[
    #     int,
    #     Field(
    #         default=1440,
    #         ge=1,
    #         le=1440,
    #         description="Timeout value for a single provider (it does not apply to "
    #        "single tries but it is the overall timeout for a provider). If provided, "
    #         "it must be greater than 0 and equal or lower than tot_timeout_mins",
    #     ),
    # ]
    keep_last_attempt: Annotated[
        bool, Field(default=False, description="Filter deployments with matching flag")
    ]
    target_provider: Annotated[
        str | None,
        Field(
            default=None,
            description="Deployment's target provider must contain this string",
        ),
    ]
    target_region: Annotated[
        str | None,
        Field(
            default=None,
            description="Deployment's target region must contain this string",
        ),
    ]


DeploymentQueryDep = Annotated[DeploymentQuery, Query()]
