"""Module with the V1 router architecture. Include all V1 endpoints."""

from fastapi import APIRouter, Security, status

from orchestrator.auth import check_authorization
from orchestrator.v1.health.endpoints import health_router
from orchestrator.v1.schemas import ErrorMessage
from orchestrator.v1.templates.endpoints import template_router
from orchestrator.v1.users.endpoints import user_router

secured_router_v1 = APIRouter(
    responses={
        status.HTTP_401_UNAUTHORIZED: {"model": ErrorMessage},
        status.HTTP_403_FORBIDDEN: {"model": ErrorMessage},
    },
    dependencies=[Security(check_authorization)],
)
secured_router_v1.include_router(user_router)
secured_router_v1.include_router(template_router)

public_router_v1 = APIRouter()
public_router_v1.include_router(health_router)
