"""DB connection and creation details."""

from typing import Annotated

from fastapi import Depends
from sqlmodel import Session, SQLModel, create_engine

from orchestrator.config import get_settings

settings = get_settings()

if settings.DB_URL.startswith("sqlite"):
    connect_args = {"check_same_thread": False}
else:
    connect_args = {}
engine = create_engine(settings.DB_URL, connect_args=connect_args, echo=settings.DB_ECO)


def create_db_and_tables():
    SQLModel.metadata.create_all(engine)


def get_session():
    with Session(engine) as session:
        yield session


SessionDep = Annotated[Session, Depends(get_session)]
