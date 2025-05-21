"""Tests for the orchestrator.__init__ module."""

from unittest import mock

import pytest

import orchestrator.__init__ as orchestrator_init


@pytest.mark.asyncio
async def test_lifespan_calls_dependencies():
    """Test that `lifespan` correctly calls its dependencies.

    This test verifies:
    - The logger is obtained and returned in the context.
    - The `configure_flaat` and `create_db_and_tables` functions are called with the
        expected arguments.
    - The `dispose_engine` function is not called until the context is exited.
    - Upon exiting the context, `dispose_engine` is called with the logger.

    Mocks are used to patch dependencies and assert their invocation.
    """
    # Patch dependencies
    with (
        mock.patch.object(orchestrator_init, "get_logger") as mock_get_logger,
        mock.patch.object(orchestrator_init, "configure_flaat") as mock_configure_flaat,
        mock.patch.object(
            orchestrator_init, "create_db_and_tables"
        ) as mock_create_db_and_tables,
        mock.patch.object(orchestrator_init, "dispose_engine") as mock_dispose_engine,
    ):
        mock_logger = mock.Mock()
        mock_get_logger.return_value = mock_logger

        # Create a dummy FastAPI app
        dummy_app = mock.Mock()

        # Use the async context manager
        cm = orchestrator_init.lifespan(dummy_app)
        # __aenter__ yields the dict
        result = await cm.__aenter__()
        assert result == {"logger": mock_logger}

        # Check that dependencies were called as expected
        mock_get_logger.assert_called_once_with(orchestrator_init.settings)
        mock_configure_flaat.assert_called_once_with(
            orchestrator_init.settings, mock_logger
        )
        mock_create_db_and_tables.assert_called_once_with(mock_logger)
        mock_dispose_engine.assert_not_called()  # Not called until exit

        # Now exit the context and check dispose_engine is called
        await cm.__aexit__(None, None, None)
        mock_dispose_engine.assert_called_once_with(mock_logger)
