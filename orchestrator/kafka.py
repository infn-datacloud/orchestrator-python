"""Backgound and asynchronous functions used to send data to kafka."""

import json
import uuid
from logging import Logger
from typing import Annotated, Any

import aiokafka.errors
from aiokafka import AIOKafkaProducer
from aiokafka.helpers import create_ssl_context
from pydantic import AnyHttpUrl, BaseModel, Field

from orchestrator.config import Settings
from orchestrator.exceptions import KafkaConnectionError
from orchestrator.v1.models import Deployment


class CreateDepMessage(BaseModel):
    """Message to send to the kafka topic devoted to deployment creation."""

    msg_version: Annotated[str, Field(description="Kafka message version")]
    deployment_id: Annotated[uuid.UUID, Field(description="Deplouyment UUID in the DB")]
    template: Annotated[str, Field(description="TOSCA template")]
    template_inputs: Annotated[
        dict[str, Any], Field(description="Dictionary with the TOSCA template inputs")
    ]
    user_group: Annotated[
        str,
        Field(description="User group owning the resources used for this deployment"),
    ]
    user_group_issuer: Annotated[AnyHttpUrl, Field(description="User group's issuer")]
    per_provider_max_retries: Annotated[
        int,
        Field(
            default=3,
            ge=1,
            le=10,
            description="Maximum number of retries for each provider. In range [1,10].",
        ),
    ]
    max_providers: Annotated[
        int | None,
        Field(
            default=None,
            ge=1,
            description="The maximum number of cloud providers on which attempt to "
            "create the deployment. In range [1, +inf)",
        ),
    ]
    timeout: Annotated[
        int,
        Field(
            default=14400,
            ge=1,
            le=14400,
            description="Overall timeout value in minutes. It must be greater than 0. "
            "In range [1,14400]",
        ),
    ]
    per_provider_timeout: Annotated[
        int,
        Field(
            default=1440,
            ge=1,
            le=1440,
            description="Timeout value for a single provider (it does not apply to "
            "single tries but it is the overall timeout for a provider). If provided, "
            "it must be greater than 0 and equal or lower than tot_timeout_mins",
        ),
    ]
    keep_last_attempt: Annotated[
        bool,
        Field(
            default=False,
            description="Whether the IM, in case of failure, will keep the resources "
            "of the last attempted deployment or not.",
        ),
    ]
    target_provider_name: Annotated[
        str | None,
        Field(default=None, description="Name of the target provider to use"),
    ]
    target_provider_type: Annotated[
        str | None,
        Field(default=None, description="Type of the target provider to use"),
    ]
    target_region_name: Annotated[
        str | None, Field(default=None, description="Name of the target region to use")
    ]
    owners_ssh_keys: Annotated[
        list[str], Field(description="List of SSH public keys of deployment owners")
    ]
    access_token: Annotated[
        str, Field(description="User's access token to send to the IM")
    ]
    refresh_token: Annotated[
        str, Field(description="User's refresh token for longer deployments")
    ]


def add_ssl_parameters(settings: Settings) -> dict[str, Any]:
    """Add SSL configuration parameters for Kafka connection based on provided settings.

    This function constructs a dictionary of SSL-related keyword arguments required for
    secure Kafka communication.

    Args:
        settings (Settings): The settings object containing Kafka SSL configurations.

    Returns:
        dict[str, Any]: A dictionary containing SSL configuration parameters for Kafka.

    Raises:
        ValueError: If the KAFKA_SSL_PASSWORD is None when SSL is enabled.

    """
    if settings.KAFKA_SSL_PASSWORD is None:
        raise ValueError(
            "KAFKA_SSL_PASSWORD can't be None when KAFKA_SSL_ENABLE is True"
        )
    context = create_ssl_context(
        ssl_cafile=settings.KAFKA_SSL_CACERT_PATH,
        ssl_certfile=settings.KAFKA_SSL_CERT_PATH,
        ssl_keyfile=settings.KAFKA_SSL_KEY_PATH,
        ssl_password=settings.KAFKA_SSL_PASSWORD,
    )
    return {"security_protocol": "SSL", "ssl_context": context}


def create_kafka_producer(
    settings: Settings, logger: Logger
) -> AIOKafkaProducer | None:
    """Create and configure a KafkaProducer instance based on the provided settings.

    This function sets up a Kafka producer with JSON value serialization, idempotence,
    and other options as specified in the `settings` object. If SSL is enabled, it loads
    the necessary SSL certificates and password from the provided paths.

    Args:
        settings (Settings): Configuration object containing Kafka connection and
            security settings.
        logger (Logger): Logger instance for logging errors and information.

    Returns:
        AIOKafkaProducer: Configured Kafka producer instance.

    """
    kwargs = {
        "client_id": settings.KAFKA_CLIENT_NAME,
        "bootstrap_servers": settings.KAFKA_BOOTSTRAP_SERVERS,
        "value_serializer": lambda x: json.dumps(x, sort_keys=True).encode("utf-8"),
        "max_request_size": settings.KAFKA_MAX_REQUEST_SIZE,
        "acks": "all",
        "enable_idempotence": True,
    }

    try:
        if settings.KAFKA_SSL_ENABLE:
            logger.info("SSL enabled")
            ssl_kwargs = add_ssl_parameters(settings=settings)
            kwargs = {**kwargs, **ssl_kwargs}

        return AIOKafkaProducer(**kwargs)

    except Exception as e:
        msg = f"Failed to create producer: {e.args[0]}"
        logger.error(msg)


async def send(producer: AIOKafkaProducer, topic: str, message: dict[str, Any]) -> None:
    """Send a message to a specified Kafka topic using an asynchronous producer.

    This function starts the given AIOKafkaProducer, sends the provided message to the
    specified topic, and ensures the producer is stopped after the operation, regardless
    of success or failure.

    Args:
        producer (AIOKafkaProducer): The asynchronous Kafka producer instance.
        topic (str): The name of the Kafka topic to send the message to.
        message (dict[str, Any]): The message payload to send.

    Returns:
        None

    Raises:
        Any exceptions raised by producer.start(), producer.send_and_wait(), or
        producer.stop() will propagate.

    """
    await producer.start()
    try:
        await producer.send_and_wait(topic, message)
    finally:
        await producer.stop()


async def send_deployment_creation(
    *,
    deployment: Deployment,
    access_token: str,
    refresh_token: str,
    settings: Settings,
    logger: Logger,
) -> None:
    """Asynchronously send message to Kafka to create a deployment.

    Args:
        deployment (Deployment): The deployment object.
        access_token (str): User access token.
        refresh_token (str): User refresh token.
        settings (Settings): Application settings including Kafka configuration and
            message version.
        logger (Logger): Logger instance for logging events.

    Returns:
        None

    Raises:
        StopIteration: If no root project is found in deployment.projects.
        Exception: Propagates exceptions from Kafka producer creation or message sending

    """
    try:
        producer = create_kafka_producer(settings, logger)
        owners_ssh_keys = [owner.public_ssh_key for owner in deployment.owned_by]
        message = CreateDepMessage(
            msg_version=settings.KAFKA_CREATE_DEP_MSG_VERSION,
            access_token=access_token,
            refresh_token=refresh_token,
            template=deployment.template.content,
            target_provider_type=deployment.template.target_provider_type,
            owners_ssh_keys=owners_ssh_keys,
            deployment_id=deployment.id,
            **deployment.model_dump(),
        )
        await send(producer, settings.KAFKA_CREATE_DEP_TOPIC, message.model_dump_json())
    except aiokafka.errors.KafkaConnectionError as e:
        raise KafkaConnectionError(e.args[0]) from e
