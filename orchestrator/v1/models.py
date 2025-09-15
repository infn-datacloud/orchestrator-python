"""DB Models for orchestrator v1.

Remember: Avoid Annotated when using Relationship
"""

import uuid
from typing import Annotated

from sqlmodel import Field, Relationship, SQLModel, UniqueConstraint

from orchestrator.v1.deployments.schemas import DeploymentBase, DeploymentInternal
from orchestrator.v1.schemas import CreationTime, ItemID, UpdateTime
from orchestrator.v1.templates.schemas import TemplateBase, TemplateUpdate
from orchestrator.v1.users.schemas import UserBase, UserUpdate


class OwnedDeployments(SQLModel, table=True):
    """Association table linking users to owned deployments."""

    owner_id: Annotated[
        uuid.UUID,
        Field(
            foreign_key="user.id",
            primary_key=True,
            description="FK pointing to the user's ID",
        ),
    ]
    deployment_id: Annotated[
        uuid.UUID,
        Field(
            foreign_key="deployment.id",
            primary_key=True,
            description="FK pointing to the deployment's ID",
        ),
    ]


class User(ItemID, CreationTime, UserBase, UserUpdate, table=True):
    """Schema used to return User's data to clients."""

    created_templates: list["Template"] = Relationship(
        back_populates="created_by",
        sa_relationship_kwargs={"foreign_keys": "Template.created_by_id"},
    )
    updated_templates: list["Template"] = Relationship(
        back_populates="updated_by",
        sa_relationship_kwargs={"foreign_keys": "Template.updated_by_id"},
    )

    created_deployments: list["Deployment"] = Relationship(
        back_populates="created_by",
        sa_relationship_kwargs={"foreign_keys": "Deployment.created_by_id"},
    )
    updated_deployments: list["Deployment"] = Relationship(
        back_populates="updated_by",
        sa_relationship_kwargs={"foreign_keys": "Deployment.updated_by_id"},
    )
    owned_deployments: list["Deployment"] = Relationship(
        back_populates="owned_by", link_model=OwnedDeployments
    )

    __table_args__ = (
        UniqueConstraint("sub", "issuer", name="unique_sub_issuer_couple"),
    )
    __hash__ = object.__hash__


class Template(
    ItemID,
    CreationTime,
    UpdateTime,
    TemplateBase,
    TemplateUpdate,
    table=True,
):
    """Schema used to return User's data to clients."""

    hash_content: Annotated[
        str, Field(unique=True, description="TOSCA template content's hash (SHA256)")
    ]

    created_by_id: Annotated[
        uuid.UUID,
        Field(foreign_key="user.id", description="User who created this item."),
    ]
    created_by: User = Relationship(
        back_populates="created_templates",
        sa_relationship_kwargs={"foreign_keys": "Template.created_by_id"},
    )

    updated_by_id: Annotated[
        uuid.UUID,
        Field(foreign_key="user.id", description="User who last updated this item."),
    ]
    updated_by: User = Relationship(
        back_populates="updated_templates",
        sa_relationship_kwargs={"foreign_keys": "Template.updated_by_id"},
    )

    deployments: list["Deployment"] = Relationship(back_populates="template")


class Deployment(
    ItemID, CreationTime, UpdateTime, DeploymentBase, DeploymentInternal, table=True
):
    """Schema used to return Deployment's data to clients."""

    created_by_id: Annotated[
        uuid.UUID,
        Field(foreign_key="user.id", description="User who created this item."),
    ]
    created_by: User = Relationship(
        back_populates="created_deployments",
        sa_relationship_kwargs={"foreign_keys": "Deployment.created_by_id"},
    )

    updated_by_id: Annotated[
        uuid.UUID,
        Field(foreign_key="user.id", description="User who last updated this item."),
    ]
    updated_by: User = Relationship(
        back_populates="updated_deployments",
        sa_relationship_kwargs={"foreign_keys": "Deployment.updated_by_id"},
    )

    owned_by: list[User] = Relationship(
        back_populates="owned_deployments", link_model=OwnedDeployments
    )

    template: Template = Relationship(back_populates="deployments")
