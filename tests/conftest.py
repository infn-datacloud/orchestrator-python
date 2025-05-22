"""Fixtures for orchestrator-python tests."""

from unittest import mock

import pytest
from fastapi.testclient import TestClient

from orchestrator import app, sub_app_v1
from orchestrator.auth import has_admin_access, has_user_access


@pytest.fixture
def client():
    """Fixture that returns a FastAPI TestClient for the app.

    Patch authentication dependencies to always allow access for tests
    """
    with TestClient(app, headers={"Authorization": "Bearer fake-token"}) as test_client:
        sub_app_v1.dependency_overrides[has_user_access] = lambda: True
        sub_app_v1.dependency_overrides[has_admin_access] = lambda: True
        yield test_client


@pytest.fixture
def session():
    """Create and return a mock session object for testing purposes.

    Returns:
        unittest.mock.Mock: A mock session object.

    """
    return mock.Mock()


@pytest.fixture
def mock_logger():
    """Fixture that returns a mock logger object for testing purposes."""
    logger = mock.Mock()
    return logger
