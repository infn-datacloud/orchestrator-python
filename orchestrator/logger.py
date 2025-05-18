"""Logger modules."""

import logging

from orchestrator.config import Settings


def get_logger(settings: Settings) -> logging.Logger:
    """Create logger"""
    formatter = logging.Formatter(
        "%(asctime)s %(levelname)s %(name)s [%(processName)s: %(process)d - "
        "%(threadName)s: %(thread)d] %(message)s"
    )

    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(formatter)

    logger = logging.getLogger("orchestrator-api")
    logger.setLevel(level=settings.LOG_LEVEL)
    logger.addHandler(stream_handler)

    return logger
