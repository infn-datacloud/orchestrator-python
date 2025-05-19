"""Authentication and authorization rules."""

import urllib.parse
from logging import Logger

import requests
from fastapi import status
from fastapi.security import HTTPBearer
from flaat.config import AccessLevel
from flaat.fastapi import Flaat
from flaat.requirements import AllOf, HasSubIss, IsTrue
from flaat.user_infos import UserInfos
from pydantic import AnyHttpUrl, EmailStr
from requests.exceptions import ConnectionError, Timeout

from orchestrator.config import AuthorizationMethodsEnum, Settings

IDP_TIMEOUT = 5
OPA_TIMEOUT = 5

security = HTTPBearer()

flaat = Flaat()


def configure_auth(settings: Settings, logger: Logger) -> None:
    """Configure flaat authentication, and OPA or flaat authorization."""
    logger.info("Set trusted IDPs: %s", settings.TRUSTED_IDP_LIST)
    logger.info("Authorization mode is %s", settings.AUTHZ_MODE.value)
    flaat.set_request_timeout(IDP_TIMEOUT)
    flaat.set_trusted_OP_list(settings.TRUSTED_IDP_LIST)
    if settings.AUTHZ_MODE == AuthorizationMethodsEnum.email:
        flaat.set_access_levels(
            [
                AccessLevel("is_admin", AllOf(HasSubIss(), IsTrue(local_is_admin)))
            ]  # TODO: With this configuration local_is_admin can accept only user_infos
        )


def local_is_admin(
    *, user_infos: UserInfos, admin_emails: list[EmailStr], logger: Logger
) -> bool:
    """Check user's email is in the list of admin emails"""
    logger.info("Verifying user email")
    email = user_infos.user_info.get("email", None)
    if email is not None:
        return email in admin_emails
    return False


def opa_is_admin(*, token: str, opa_roles_endpoint: AnyHttpUrl, logger: Logger) -> bool:
    """Contact OPA to verify if the user belongs to the administrators group"""
    data = {"input": {"authorization": f"Bearer {token}"}}
    try:
        logger.info("Sending user's token to OPA")
        resp = requests.post(
            urllib.parse.urljoin(str(opa_roles_endpoint), "is_admin"),
            json=data,
            timeout=OPA_TIMEOUT,
        )
        if resp.status_code == status.HTTP_200_OK:
            is_admin = resp.json().get("result", False)
            logger.info("User is %s admin", "" if is_admin else "not")
            return is_admin

        if resp.status_code == status.HTTP_400_BAD_REQUEST:
            raise ConnectionRefusedError(
                "Authentication failed: Bad request sent to OPA server."
            )
        if resp.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR:
            raise ConnectionRefusedError(
                "Authentication failed: OPA server internal error."
            )
        raise ConnectionRefusedError(
            f"Authentication failed: OPA unexpected response code '{resp.status_code}'."
        )
    except (Timeout, ConnectionError) as e:
        raise ConnectionRefusedError(
            "Authentication failed: OPA server is not reachable."
        ) from e


def is_admin(*, token: str, settings: Settings, logger: Logger) -> bool:
    """Validate received token and verify needed rights.

    Contact OPA to verify if the target user has the requested role.
    """
    if settings.AUTHZ_MODE == AuthorizationMethodsEnum.email:
        user_infos = flaat.get_user_infos_from_access_token(token)
        return local_is_admin(
            user_infos=user_infos, admin_emails=settings.ADMIN_EMAIL_LIST, logger=logger
        )
    if settings.AUTHZ_MODE == AuthorizationMethodsEnum.opa:
        return opa_is_admin(
            token=token, opa_roles_endpoint=settings.OPA_AUTHZ_URL, logger=logger
        )
