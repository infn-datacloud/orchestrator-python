"""Fixtures for orchestrator-python tests."""

from unittest import mock

import pytest


@pytest.fixture
def session():
    """Create and return a mock session object for testing purposes.

    Returns:
        unittest.mock.Mock: A mock session object.

    """
    return mock.Mock()
