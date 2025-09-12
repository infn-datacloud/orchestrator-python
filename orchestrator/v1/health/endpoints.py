"""Endpoints to manage User details."""

import urllib.parse

import requests
from fastapi import APIRouter, Request, status
from requests.exceptions import ConnectionError

from orchestrator.config import AuthorizationMethodsEnum, SettingsDep
from orchestrator.db import SessionDep
from orchestrator.v1 import HEALTH_PREFIX
from orchestrator.v1.health.schemas import Health

health_router = APIRouter(prefix=HEALTH_PREFIX, tags=["health"])


@health_router.get(
    "/", summary="Get application health", response_model_exclude_none=True
)
async def liveness_probe(
    request: Request, session: SessionDep, settings: SettingsDep
) -> Health:
    """Retrieve service healthness.

    Check connection with related services.

    Args:
        request (Request): The incoming HTTP request object, used for logging.
        session (SessionDep): Database session dependency.
        settings (SettingsDep): Dependency containing app settings.

    Returns:
        Health: single connections status and general service status.

    """
    data = {}
    data["db_connection"] = not session.connection().closed
    if settings.AUTHZ_MODE == AuthorizationMethodsEnum.opa:
        try:
            resp = requests.get(
                urllib.parse.urljoin(str(settings.OPA_AUTHZ_URL), "health"),
                timeout=settings.OPA_TIMEOUT,
            )
            data["opa_connection"] = resp.status_code == status.HTTP_200_OK
        except ConnectionError:
            data["opa_connection"] = False
    if settings.VAULT_ENABLE:
        ...
    if settings.KAFKA_ENABLE:
        ...
    return Health(**data).model_dump()
