"""Utilities to communicat with the Hashicorp Vault."""

import urllib.parse
from logging import Logger

import hvac
import hvac.exceptions
import requests
import urllib3
from hvac.api.auth_methods import Token
from pydantic import AnyHttpUrl

from orchestrator.config import Settings
from orchestrator.exceptions import VaultConnectionError
from orchestrator.iam import exchange_token_with_audience

PRIV_KEY_ID = "ssh_private_key"

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)  # TODO Remove


class VaultClient:
    """Client for the Hashicorp vault."""

    def __init__(
        self,
        *,
        url: AnyHttpUrl,
        mount_point: str,
        role: str,
        token_ttl: int,
        token_period: int,
        read_policy: str,
        write_policy: str,
        delete_policy: str,
        logger: Logger,
    ) -> None:
        """Initialize client."""
        self.vault_url = url
        self.mount_point = mount_point
        self.role = role
        self.token_ttl = token_ttl
        self.token_period = token_period
        self.read_policy = read_policy
        self.write_policy = write_policy
        self.delete_policy = delete_policy
        self.logger = logger

    def __set_token(self, policy: str) -> str:
        """Get Vault token with specific policy.

        POST '/v1/auth/token/create'

        Args:
            policy (str): Policy name to get token authorization scopes.
            ttl (int): token duration (time to leave)
            period (int): token renewal time.

        Returns:
            str: the vault token

        """
        token = Token(self.client.adapter).create(
            policies=[policy], ttl=self.token_ttl, period=self.token_period
        )
        self.client.token = token["auth"]["client_token"]
        if not self.client.is_authenticated():
            msg = f"Error authenticating against Vault with token: {self.client.token}"
            self.logger.error(msg)
            raise VaultConnectionError(msg)

    def connect(self, jwt_token: str, policy: str) -> None:
        """Connect to vault with the user JWT access token.

        Args:
            jwt_token (str): User JWT access token.
            policy (str): Generate token with the given policy.

        Returns:
            None

        """
        login_url = urllib.parse.urljoin(self.vault_url, "v1/auth/jwt/login")
        data = {"jwt": jwt_token, "role": self.role}
        resp = requests.post(
            login_url, json=data, verify=False
        )  # TODO remove verify=False
        if not resp.ok:
            msg = f"Error authenticating against Vault with token '{jwt_token}' and "
            msg += f"role '{self.role}'"
            self.logger.error(msg)
            raise VaultConnectionError(msg)

        data = resp.json()
        self.vault_auth_token = data["auth"]["client_token"]
        self.client = hvac.Client(url=self.vault_url, token=self.vault_auth_token)
        if not self.client.is_authenticated():
            msg = "Error authenticating against Vault with token "
            msg += f"'{self.vault_auth_token}' and role '{self.role}'"
            self.logger.error(msg)
            raise VaultConnectionError(msg)
        self.__set_token(policy)

    def disconnect(self) -> None:
        """Disconnect client.

        Revoke token on logout.

        Returns:
            None

        """
        self.client.logout(revoke_token=True)

    def write_secret(
        self, *, secret_path: str, key: str, value: str, cas: int = 0
    ) -> None:
        """Write secret to Vault.

        POST '/v1/'+self.secrets_root+'/data/' + secret_path

        Args:
            jwt_token (str): Access token (JWT) with the audience.
            secret_path (str): Path where to write the secret key and value.
            key (str): Secret key.
            value (str): Secret value.
            cas (int): ...

        Returns:
            None

        """
        try:
            response = self.client.secrets.kv.v2.create_or_update_secret(
                path=secret_path,
                mount_point=self.mount_point,
                secret={key: value},
                cas=cas,
            )
        except hvac.exceptions.InvalidRequest as e:
            # TODO Improve error management
            msg = f"[FATAL] Unable to write vault path: {e!s}"
            self.logger.error(msg)
            raise Exception(msg) from e
        return response

    def delete_secret(self, *, secret_path: str) -> None:
        """Permanently delete secret and metadata from Vault.

        Open connection, delete secret and revoke used token.
        Delete_url = self.vault_url+'/v1/'+self.secrets_root+'/metadata/'+secret_path

        Args:
            jwt_token (str): Access token (JWT) with the audience.
            secret_path (str): All elements in this path will be delete.

        Returns:
            None

        Raises:
            VaultConnectionError: Connection with vault fails.

        """
        try:
            self.client.secrets.kv.v2.delete_metadata_and_all_versions(
                path=secret_path, mount_point=self.mount_point
            )
        except hvac.exceptions.InvalidRequest as e:
            # TODO Improve error management
            msg = f"[FATAL] Unable to delete vault path: {e!s}"
            self.logger.error(msg)
            raise Exception(msg) from e


def create_vault_client(settings: Settings, logger: Logger) -> VaultClient:
    """Create a vault client instance.

    Args:
        settings (Settings): Application settings.
        logger (Logger): Logger instance.

    Returns:
        VaultClient: vault client instance.

    """
    return VaultClient(
        vault_url=settings.VAULT_URL,
        mount_point=settings.VAULT_SECRETS_PATH,
        role=settings.VAULT_ROLE,
        token_ttl=settings.VAULT_TOKEN_DURATION,
        token_period=settings.VAULT_TOKEN_RENEWAL_DURATION,
        read_policy=settings.VAULT_READ_POLICY,
        write_policy=settings.VAULT_WRITE_POLICY,
        delete_policy=settings.VAULT_DELETE_POLICY,
        logger=logger,
    )


def store_private_key(
    *,
    private_key: str,
    issuer: str,
    sub: str,
    access_token: str,
    vault_client: VaultClient,
    settings: Settings,
    logger: Logger,
) -> None:
    """Store the private key in the hashicorp vault.

    Args:
        private_key (str): Private key to store in vault.
        issuer (str): Identity provider's issuer
        sub (str): User subject
        access_token (str): User access token
        vault_client (VaultClient): Vault client instance
        settings (Settings): Application settings
        logger (Logger): Logger instance

    Returns:
        None

    """
    secret_path = f"{sub}/{PRIV_KEY_ID}"
    jwt_token = exchange_token_with_audience(
        issuer=issuer, token=access_token, settings=settings, logger=logger
    )
    vault_client.connect(jwt_token)
    response_output = vault_client.write_secret(
        jwt_token=jwt_token, secret_path=secret_path, key=PRIV_KEY_ID, value=private_key
    )
    vault_client.disconnect()
    return response_output


def delete_private_key(
    *,
    issuer: str,
    sub: str,
    access_token: str,
    vault_client: VaultClient,
    settings: Settings,
    logger: Logger,
) -> None:
    """Delete the private key from the hashicorp vault.

    Args:
        issuer (str): Identity provider's issuer
        sub (str): User subject
        access_token (str): User access token
        vault_client (VaultClient): Vault client instance
        settings (Settings): Application settings
        logger (Logger): Logger instance

    Returns:
        None

    """
    secret_path = f"{sub}/{PRIV_KEY_ID}"
    jwt_token = exchange_token_with_audience(
        issuer=issuer, token=access_token, settings=settings, logger=logger
    )
    vault_client.connect(jwt_token)
    vault_client.delete_secret(jwt_token=jwt_token, secret_path=secret_path)
    vault_client.disconnect()
