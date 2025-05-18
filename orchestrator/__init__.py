"""Entry point for the Federation-Registry web app."""

import urllib.parse
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from orchestrator.config import API_V1_STR, get_settings
from orchestrator.db import create_db_and_tables, dispose_engine
from orchestrator.logger import get_logger
from orchestrator.v1.router import router as router_v1

settings = get_settings()

summary = "Orchestrator REST API of the DataCloud project"
description = "The Orchestrator component stores users' deployments details."
version = "0.1.0"
contact = {
    "name": settings.MAINTAINER_NAME,
    "url": settings.MAINTAINER_URL,
    "email": settings.MAINTAINER_EMAIL,
}
tags_metadata = [
    {
        "name": API_V1_STR,
        "description": "API version 1, see link on the right",
        "externalDocs": {
            "description": "API version 1 documentation",
            "url": urllib.parse.urljoin(str(settings.BASE_URL), API_V1_STR + "docs"),
        },
    },
]


@asynccontextmanager
async def lifespan(app: FastAPI):
    """App Context Manager.

    Create logger and make it available in the requests' state. Connect and disconnect
    from DB.
    """
    logger = get_logger(settings)
    create_db_and_tables(logger)
    yield {"logger": logger}
    dispose_engine(logger)


app = FastAPI(
    contact=contact,
    description=description,
    openapi_tags=tags_metadata,
    summary=summary,
    title=settings.PROJECT_NAME,
    version=version,
    lifespan=lifespan,
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[str(origin) for origin in settings.BACKEND_CORS_ORIGINS],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

sub_app_v1 = FastAPI(
    contact=contact,
    description=description,
    summary=summary,
    title=settings.PROJECT_NAME,
    version=version,
)
sub_app_v1.include_router(router_v1)
app.mount(API_V1_STR, sub_app_v1)
