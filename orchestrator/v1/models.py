"""DB Models for orchestrator v1.

Remember: Avoid Annotated when using Relationship
"""

from sqlmodel import UniqueConstraint

from orchestrator.v1.schemas import CreationTime, ItemID
from orchestrator.v1.users.schemas import UserCreate, UserUpdate


class User(ItemID, CreationTime, UserCreate, UserUpdate, table=True):
    """Schema used to return User's data to clients."""

    __table_args__ = (
        UniqueConstraint("sub", "issuer", name="unique_sub_issuer_couple"),
    )
    __hash__ = object.__hash__
