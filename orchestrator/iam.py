"""Utilities to communicate with IAM identity provider."""

from logging import Logger
from urllib.parse import urljoin

import requests

from orchestrator.config import Settings
from orchestrator.exceptions import ConfigurationError, IdentityProviderConnectionError


def exchange_token_with_audience(
    *, issuer: str, token: str, settings: Settings, logger: Logger
) -> str:
    """Retrieve an access token with the given token.

    Send the current token and add the target audience.

    Args:
        issuer (str): IAM endpoint.
        token (str): User access token.
        settings (Settings): Settings instance to retrieve client's id and secret.
        logger (Logger): Logger instance.

    Returns:
        str: The new token with the audience

    """
    url = urljoin(issuer, "token")

    client_id = None
    client_secret = None
    for idp in settings.TRUSTED_IDP_LIST:
        if idp.issuer == issuer:
            client_id = idp.client_id
            client_secret = idp.client_secret
            break
    if client_id is None or client_secret is None:
        msg = f"No trusted identity provider with issuer={issuer}"
        logger.erro(msg)
        raise ConfigurationError(msg)

    payload = {
        "grant_type": "urn:ietf:params:oauth:grant-type:token-exchange",
        "audience": settings.VAULT_BOUND_AUDIENCE,
        "subject_token": token,
        "scope": "openid profile",
    }
    resp = requests.post(url, json=payload, auth=(client_id, client_secret))

    if not resp.ok:
        msg = f"Error exchanging token: {resp.status_code} - {resp.text}"
        logger.error(msg)
        raise IdentityProviderConnectionError(msg)

    data = resp.json()
    return data["access_token"]
