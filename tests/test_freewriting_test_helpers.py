"""Tests for freewriting test helpers."""

from unittest.mock import Mock, patch

from prosemark.freewriting.test_helpers import (
    create_integration_tui_mock,
    create_title_processing_mock,
)


class TestCreateTitleProcessingMock:
    """Test the create_title_processing_mock helper function."""

    def test_returns_original_mock_when_no_title(self) -> None:
        """Test that original mock is returned when title is None."""
        original_mock = Mock()
        original_side_effect = original_mock.side_effect

        result = create_title_processing_mock(original_mock, title=None)

        assert result is original_mock
        # Side effect should remain unchanged
        assert result.side_effect == original_side_effect

    def test_returns_original_mock_when_empty_title(self) -> None:
        """Test that original mock is returned when title is empty string."""
        original_mock = Mock()
        original_side_effect = original_mock.side_effect

        result = create_title_processing_mock(original_mock, title='')

        assert result is original_mock
        # Side effect should remain unchanged
        assert result.side_effect == original_side_effect

    def test_enhances_mock_with_side_effect_when_title_provided(self) -> None:
        """Test that mock is enhanced with side_effect when title is provided."""
        original_mock = Mock()
        original_side_effect = original_mock.side_effect
        title = 'Test Title'

        result = create_title_processing_mock(original_mock, title=title)

        assert result is original_mock
        # Side effect should have changed
        assert result.side_effect != original_side_effect
        assert callable(result.side_effect)

    def test_side_effect_processes_title_from_args(self) -> None:
        """Test that side_effect processes title from session_config argument."""
        original_mock = Mock()
        title = 'Test Title'
        session_config_mock = Mock()
        session_config_mock.title = title

        # Mock the process_title function
        with patch('prosemark.freewriting.test_helpers.process_title') as mock_process_title:
            enhanced_mock = create_title_processing_mock(original_mock, title=title)

            # Call the side_effect with a session_config
            result = enhanced_mock.side_effect(session_config_mock)

            # Verify process_title was called with the session_config title
            mock_process_title.assert_called_once_with(title)

            # Verify the returned mock has the expected structure
            assert isinstance(result, Mock)
            assert hasattr(result, 'run')

    def test_side_effect_processes_fallback_title(self) -> None:
        """Test that side_effect processes fallback title when no session_config title."""
        original_mock = Mock()
        title = 'Fallback Title'

        # Mock the process_title function
        with patch('prosemark.freewriting.test_helpers.process_title') as mock_process_title:
            enhanced_mock = create_title_processing_mock(original_mock, title=title)

            # Call the side_effect with an object that doesn't have title attribute
            result = enhanced_mock.side_effect(123)

            # Verify process_title was called with the fallback title
            mock_process_title.assert_called_once_with(title)

            # Verify the returned mock has the expected structure
            assert isinstance(result, Mock)
            assert hasattr(result, 'run')
            assert result.run.return_value is None


class TestCreateIntegrationTuiMock:
    """Test the create_integration_tui_mock helper function."""

    def test_modifies_mock_tui_class_with_side_effect(self) -> None:
        """Test that the function adds a side_effect to the mock TUI class."""
        mock_tui_class = Mock()

        create_integration_tui_mock(mock_tui_class)

        assert hasattr(mock_tui_class, 'side_effect')
        assert callable(mock_tui_class.side_effect)

    def test_side_effect_calls_initialize_session(self) -> None:
        """Test that the side_effect calls tui_adapter.initialize_session."""
        mock_tui_class = Mock()
        mock_session_config = Mock()
        mock_tui_adapter = Mock()

        create_integration_tui_mock(mock_tui_class)

        # Call the side_effect (simulating TUI construction)
        result = mock_tui_class.side_effect(mock_session_config, mock_tui_adapter, some_kwarg='value')

        # Verify initialize_session was called
        mock_tui_adapter.initialize_session.assert_called_once_with(mock_session_config)

        # Verify the returned mock has the expected structure
        assert isinstance(result, Mock)
        assert hasattr(result, 'run')
        assert result.run.return_value is None

    def test_side_effect_accepts_additional_kwargs(self) -> None:
        """Test that the side_effect accepts and ignores additional kwargs."""
        mock_tui_class = Mock()
        mock_session_config = Mock()
        mock_tui_adapter = Mock()

        create_integration_tui_mock(mock_tui_class)

        # Call with additional kwargs
        result = mock_tui_class.side_effect(
            mock_session_config, mock_tui_adapter, theme='dark', debug=True, extra_arg='ignored'
        )

        # Should still work and call initialize_session
        mock_tui_adapter.initialize_session.assert_called_once_with(mock_session_config)
        assert isinstance(result, Mock)
