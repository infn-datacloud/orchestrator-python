"""Authentication and authorization rules."""

from logging import Logger
from typing import Annotated

from fastapi import HTTPException, Request, Security, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from flaat import AuthWorkflow
from flaat.config import AccessLevel
from flaat.exceptions import FlaatForbidden, FlaatUnauthenticated
from flaat.fastapi import Flaat
from flaat.requirements import AllOf, HasSubIss, get_claim_requirement
from flaat.user_infos import UserInfos

from orchestrator.config import AuthorizationMethodsEnum, Settings, SettingsDep

IDP_TIMEOUT = 5
OPA_TIMEOUT = 5

flaat = Flaat()


def configure_flaat(settings: Settings, logger: Logger) -> None:
    """Configure the Flaat authentication and authorization system for the application.

    Sets trusted identity providers, request timeouts, and access levels based on the
    application's authorization mode (email or groups). This function should be called
    at application startup.

    Args:
        settings: The application settings instance.
        logger: The logger instance for logging configuration details.

    """
    logger.info("Set trusted IDPs: %s", settings.TRUSTED_IDP_LIST)
    logger.info("Authorization mode is %s", settings.AUTHZ_MODE.value)
    flaat.set_request_timeout(IDP_TIMEOUT)
    flaat.set_trusted_OP_list([str(i) for i in settings.TRUSTED_IDP_LIST])
    if settings.AUTHZ_MODE in [
        AuthorizationMethodsEnum.email,
        AuthorizationMethodsEnum.groups,
    ]:
        if settings.AUTHZ_MODE == AuthorizationMethodsEnum.email:
            required = settings.ADMIN_EMAIL_LIST
        else:
            required = settings.ADMIN_GROUP_LIST
        email_requirement = get_claim_requirement(
            required=required, claim=AuthorizationMethodsEnum.email, match=1
        )
        flaat.set_access_levels(
            [
                AccessLevel("is_user", AllOf(HasSubIss())),
                AccessLevel("is_admin", AllOf(HasSubIss(), email_requirement)),
            ]
        )


security = HTTPBearer()

HttpAuthzCredsDep = Annotated[HTTPAuthorizationCredentials, Security(security)]


def check_authentication(authz_creds: HttpAuthzCredsDep) -> UserInfos:
    """Verify that the provided access token belongs to a trusted issuer.

    Args:
        authz_creds: HTTP authorization credentials extracted from the request.

    Returns:
        UserInfos: The user information extracted from the access token.

    Raises:
        HTTPException: If the token is not valid or not from a trusted issuer.

    """
    try:
        return flaat.get_user_infos_from_access_token(authz_creds.credentials)
    except FlaatUnauthenticated as e:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail=e.render()
        ) from e


AuthenticationDep = Annotated[UserInfos, Security(check_authentication)]


def check_authorization(
    *, user_infos: UserInfos, access_level: str, settings: Settings, logger: Logger
) -> None:
    """Check user permissions based on specified access level and authorization mode.

    Args:
        user_infos: The authenticated user information.
        access_level: The required access level (e.g., 'is_user', 'is_admin').
        settings: The application settings instance.
        logger: The logger instance for logging authorization details.

    Raises:
        HTTPException: If the user does not have the required access level.

    """
    if settings.AUTHZ_MODE == AuthorizationMethodsEnum.email:
        logger.info("Authorization through local configuration: check user's email")
        auth_workflow = AuthWorkflow(
            flaat,
            user_requirements=flaat._get_access_level_requirement(access_level),
            process_arguments=settings.ADMIN_EMAIL_LIST,
        )
        try:
            auth_workflow.check_user_authorization(user_infos=user_infos)
        except FlaatForbidden as e:
            raise HTTPException(status.HTTP_401_UNAUTHORIZED, detail=e.render()) from e
    if settings.AUTHZ_MODE == AuthorizationMethodsEnum.opa:
        logger.info("Authorization through OPA")


def has_user_access(
    request: Request, user_infos: AuthenticationDep, settings: SettingsDep
) -> None:
    """Dependency to check if the current user has user-level access permissions.

    Args:
        request: The current FastAPI request object (provides logger in state).
        user_infos: The authenticated user information.
        settings: The application settings dependency.

    Raises:
        HTTPException: If the user does not have user-level access.

    """
    check_authorization(
        user_infos=user_infos,
        access_level="is_user",
        logger=request.state.logger,
        settings=settings,
    )


def has_admin_access(
    request: Request, user_infos: AuthenticationDep, settings: SettingsDep
) -> None:
    """Dependency to check if the current user has admin-level access permissions.

    Args:
        request: The current FastAPI request object (provides logger in state).
        user_infos: The authenticated user information.
        settings: The application settings dependency.

    Raises:
        HTTPException: If the user does not have admin-level access.

    """
    check_authorization(
        user_infos=user_infos,
        access_level="is_admin",
        logger=request.state.logger,
        settings=settings,
    )

