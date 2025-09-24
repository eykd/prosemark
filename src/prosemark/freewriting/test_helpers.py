"""Test helpers for freewriting integration tests."""

from __future__ import annotations

from typing import TYPE_CHECKING
from unittest.mock import Mock

from prosemark.freewriting.adapters.title_handler import process_title

if TYPE_CHECKING:
    from prosemark.freewriting.domain.models import SessionConfig  # pragma: no cover
    from prosemark.freewriting.ports.tui_adapter import TUIAdapterPort  # pragma: no cover


def create_title_processing_mock(original_mock: Mock, title: str | None = None) -> Mock:
    """Create a mock that calls process_title when instantiated.

    Args:
        original_mock: The original mock to enhance.
        title: The title to process, if any.

    Returns:
        Enhanced mock that calls process_title on instantiation.

    """
    if not title:
        return original_mock

    def side_effect(*args: object) -> Mock:
        # Extract title from session_config if available
        if args and hasattr(args[0], 'title'):
            session_config = args[0]
            if session_config.title:  # pragma: no branch
                process_title(session_config.title)
        elif title:  # pragma: no branch
            process_title(title)

        # Return the original mock instance
        mock_instance = Mock()
        mock_instance.run.return_value = None
        return mock_instance

    original_mock.side_effect = side_effect
    return original_mock


def create_integration_tui_mock(mock_tui_class: Mock) -> None:
    """Create a TUI mock for integration tests that still triggers session creation.

    Args:
        mock_tui_class: The mocked TUI class to enhance.

    This function modifies the mock to call tui_adapter.initialize_session() when
    the TUI is constructed, simulating the session creation that normally happens
    in the TUI's on_mount() method.

    """

    def mock_tui_constructor(
        session_config: SessionConfig,
        tui_adapter: TUIAdapterPort,
        **_kwargs: object,
    ) -> Mock:
        # Simulate the session initialization that normally happens in on_mount()
        tui_adapter.initialize_session(session_config)
        mock_tui = Mock()
        mock_tui.run.return_value = None
        return mock_tui

    mock_tui_class.side_effect = mock_tui_constructor
