"""Backgound functions used to send data to kafka."""

import asyncio
import json
from logging import Logger
from typing import Any

from aiokafka import AIOKafkaConsumer, ConsumerRecord
from pydantic import ValidationError

from orchestrator.config import Settings


class KafkaMessageError:
    pass


def notify_error(message: KafkaMessageError):
    pass


def consume(message: ConsumerRecord):
    try:
        message_value = message.value.decode("utf-8")
        message_data = json.loads(message_value)
        # TODO: Based on the topic's message process it
        # if message.topic == "errors":
        #     validated_message = KafkaMessageError(**message_data)
        #     return notify_error(validated_message)
    except json.JSONDecodeError as e:
        raise ValueError(f"Failed to decode Kafka message: {e}") from e
    except ValidationError as e:
        raise ValueError(f"Kafka message validation error: {e}") from e


async def start_kafka_consumer(settings: Settings, logger: Logger) -> None:
    try:
        kafka_consumer = AIOKafkaConsumer(
            "pippo", bootstrap_servers=settings.KAFKA_SERVERS
        )
        await kafka_consumer.start()

        try:
            async for message in kafka_consumer:
                consume(message)
        except Exception as e:
            message = f"Failed to consume kafka message: {e}"
            logger.error(message)

    except Exception as e:
        message = f"Failed to start Kafka consumer: {e}"
        logger.error(message)

    finally:
        await kafka_consumer.stop()


async def start_kafka_listener(settings: Logger, logger: Logger) -> asyncio.Task:
    """Start to listen on kafka topics"""
    logger.info("Start listening on Kafka topics")
    return asyncio.create_task(start_kafka_consumer(settings, logger))


async def stop_kafka_listener(kafka_task: asyncio.Task, logger: Logger) -> None:
    """Cancel previously registered task"""
    logger.info("Cancel Kafka consumers")
    kafka_task.cancel()
    try:
        await kafka_task
        logger.info("Kafka consumers canceled")
    except asyncio.CancelledError as e:
        logger.error("Failed to cancel Kafka consumers: %s", e)


def start_deployment_procedure(data: dict[str, Any]) -> None:
    """Send message to kafka topic accepting new deployment requests."""
