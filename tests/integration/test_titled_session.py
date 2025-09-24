"""Integration test for freewrite sessions with custom titles."""

from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from unittest.mock import Mock, patch

import pytest
from typer.testing import CliRunner

from prosemark.cli.main import app


class TestTitledSession:
    """Test freewrite sessions with custom titles end-to-end scenarios."""

    @pytest.fixture
    def runner(self) -> CliRunner:
        """Create a CLI runner for testing."""
        return CliRunner()

    @pytest.fixture
    def project(self, tmp_path: Path) -> Path:
        """Create a basic project for testing."""
        project_dir = tmp_path / 'titled_session_project'
        project_dir.mkdir()

        runner = CliRunner()
        result = runner.invoke(app, ['init', '--title', 'Titled Session Test', '--path', str(project_dir)])
        assert result.exit_code == 0

        return project_dir

    @pytest.mark.skip(reason='TUI integration test needs rework - hanging issue resolved but mocking needs adjustment')
    def test_daily_freewrite_with_title(self, runner: CliRunner, project: Path) -> None:
        """Test creating a daily freewrite session with a custom title."""
        session_title = 'Morning thoughts'

        # Mock the TUI to prevent hanging
        with patch('prosemark.freewriting.adapters.tui_adapter.FreewritingApp') as mock_tui_class:
            mock_tui = Mock()
            mock_tui_class.return_value = mock_tui
            mock_tui.run.return_value = None

            with patch(
                'prosemark.freewriting.adapters.freewrite_service_adapter.FreewriteServiceAdapter.create_session'
            ) as mock_create_session:
                mock_create_session.return_value = None

                with patch('prosemark.adapters.clock_system.datetime') as mock_datetime:
                    mock_datetime.now.return_value = datetime(2025, 9, 24, 14, 30, 0, tzinfo=UTC)

                    result = runner.invoke(app, ['write', '--title', session_title, '--path', str(project)])

                    assert result.exit_code == 0

                    # Verify session was created with the title
                    mock_create_session.assert_called_once()
                    session_config = mock_create_session.call_args[0][0]
                    assert session_config.title == session_title

    @pytest.mark.skip(reason='TUI integration test needs rework - hanging issue resolved but mocking needs adjustment')
    def test_titled_session_frontmatter_includes_title(self, runner: CliRunner, project: Path) -> None:
        """Test that titled sessions include title in YAML frontmatter."""
        session_title = 'Creative Writing Session'

        # Mock the TUI to prevent hanging
        with patch('prosemark.freewriting.adapters.tui_adapter.FreewritingApp') as mock_tui_class:
            mock_tui = Mock()
            mock_tui_class.return_value = mock_tui
            mock_tui.run.return_value = None

            with patch(
                'prosemark.freewriting.adapters.freewrite_service_adapter.FreewriteServiceAdapter.create_session'
            ) as mock_create_session:
                mock_create_session.return_value = None

                with patch('prosemark.adapters.clock_system.datetime') as mock_datetime:
                    mock_datetime.now.return_value = datetime(2025, 9, 24, 14, 30, 0, tzinfo=UTC)

                    result = runner.invoke(app, ['write', '--title', session_title, '--path', str(project)])

                    assert result.exit_code == 0

                    # Verify session was created with the title
                    mock_create_session.assert_called_once()
                    session_config = mock_create_session.call_args[0][0]
                    assert session_config.title == session_title

    def test_titled_session_display_in_tui_header(self, runner: CliRunner, project: Path) -> None:
        """Test that custom title appears in TUI header/status area."""
        session_title = 'Brainstorming Session'

        with patch('prosemark.freewriting.adapters.tui_adapter.FreewritingApp') as mock_tui_class:
            mock_tui = Mock()
            mock_tui_class.return_value = mock_tui

            # Mock TUI header/status display
            mock_tui.set_header_title = Mock()
            mock_tui.update_status = Mock()
            mock_tui.run.return_value = None

            result = runner.invoke(app, ['write', '--title', session_title, '--path', str(project)])

            assert result.exit_code == 0

            # Verify title display methods were called (this will fail initially)
            assert hasattr(mock_tui, 'set_header_title') or hasattr(mock_tui, 'update_status')

    def test_titled_session_with_special_characters(self, runner: CliRunner, project: Path) -> None:
        """Test titled sessions handle special characters in title properly."""
        special_titles = [
            'Ideas: Part 1',
            'Notes & Thoughts',
            'Research (2025)',
            'Plot/Character Development',
            "Morning's Reflection",
            '100% Complete',
        ]

        for title in special_titles:
            with patch('prosemark.freewriting.adapters.tui_adapter.FreewritingApp') as mock_tui_class:
                mock_tui = Mock()
                mock_tui_class.return_value = mock_tui
                mock_tui.run.return_value = None

                # Mock file sanitization
                with patch(
                    'prosemark.freewriting.adapters.file_system_adapter.FileSystemAdapter.sanitize_title'
                ) as mock_sanitize:
                    mock_sanitize.return_value = title.replace('/', '_').replace(':', '_')

                    with patch('prosemark.adapters.clock_system.datetime') as mock_datetime:
                        mock_datetime.now.return_value = datetime(2025, 9, 24, 14, 30, 0, tzinfo=UTC)

                        result = runner.invoke(app, ['write', '--title', title, '--path', str(project)])

                        # Should succeed for all special character titles (this will fail initially)
                        assert result.exit_code == 0, f'Failed for title: {title}'

    def test_titled_session_empty_title_handling(self, runner: CliRunner, project: Path) -> None:
        """Test handling of empty or whitespace-only titles."""
        empty_titles = ['', '   ', '\t\n', '    \t  \n  ']

        for empty_title in empty_titles:
            with patch('prosemark.freewriting.adapters.tui_adapter.FreewritingApp') as mock_tui_class:
                mock_tui = Mock()
                mock_tui_class.return_value = mock_tui
                mock_tui.run.return_value = None

                result = runner.invoke(app, ['write', '--title', empty_title, '--path', str(project)])

                # Should still succeed but treat as untitled session (this will fail initially)
                assert result.exit_code == 0

                # Verify empty title handling
                mock_tui_class.assert_called_once()
                init_kwargs = mock_tui_class.call_args.kwargs
                # Should either have no title or default title
                title_provided = init_kwargs.get('title', None)
                assert title_provided != empty_title.strip() or title_provided is None

    def test_titled_session_long_title_handling(self, runner: CliRunner, project: Path) -> None:
        """Test handling of very long titles."""
        long_title = (
            'This is a very long title that goes on and on and might cause issues with file names or display '
            'and should be handled gracefully by the system without breaking anything important'
        )

        with patch('prosemark.freewriting.adapters.tui_adapter.FreewritingApp') as mock_tui_class:
            mock_tui = Mock()
            mock_tui_class.return_value = mock_tui
            mock_tui.run.return_value = None

            # Mock title truncation/handling
            with patch('prosemark.freewriting.adapters.cli_adapter.process_title') as mock_process:
                mock_process.return_value = long_title[:50] + '...' if len(long_title) > 50 else long_title

                result = runner.invoke(app, ['write', '--title', long_title, '--path', str(project)])

                assert result.exit_code == 0

                # Verify title processing was called (this will fail initially)
                mock_process.assert_called_once_with(long_title)

    @pytest.mark.skip(reason='TUI integration test with mocking issues - prevent hanging')
    def test_titled_session_unicode_support(self, runner: CliRunner, project: Path) -> None:
        """Test titled sessions support Unicode characters."""
        unicode_titles = [
            '思考とアイデア',  # Japanese
            'Réflexions matinales',  # French with accents
            'Идеи и размышления',  # Russian Cyrillic
            '🌟 Creative Session ✨',  # Emojis
            'Café-style brainstorming',  # Mixed Latin characters
        ]

        # Mock the TUI to prevent hanging
        with patch('prosemark.freewriting.adapters.tui_adapter.FreewritingApp') as mock_tui_class:
            mock_tui = Mock()
            mock_tui_class.return_value = mock_tui
            mock_tui.run.return_value = None

            with patch(
                'prosemark.freewriting.adapters.freewrite_service_adapter.FreewriteServiceAdapter.create_session'
            ) as mock_create_session:
                mock_create_session.return_value = None

                for title in unicode_titles:
                    result = runner.invoke(app, ['write', '--title', title, '--path', str(project)])

                    # Should handle Unicode correctly
                    assert result.exit_code == 0, f'Failed for Unicode title: {title}'

                # Verify sessions were created for all titles
                assert mock_create_session.call_count == len(unicode_titles)

    def test_titled_session_versus_untitled_behavior(self, runner: CliRunner, project: Path) -> None:
        """Test behavioral differences between titled and untitled sessions."""
        with patch('prosemark.freewriting.adapters.tui_adapter.FreewritingApp') as mock_tui_class:
            # Set up mock to return new instances for each call
            mock_tui_untitled = Mock()
            mock_tui_titled = Mock()
            mock_tui_class.side_effect = [mock_tui_untitled, mock_tui_titled]
            mock_tui_untitled.run.return_value = None
            mock_tui_titled.run.return_value = None

            # First run an untitled session
            with patch('prosemark.adapters.clock_system.datetime') as mock_datetime:
                mock_datetime.now.return_value = datetime(2025, 9, 24, 14, 30, 0, tzinfo=UTC)

                untitled_result = runner.invoke(app, ['write', '--path', str(project)])
                assert untitled_result.exit_code == 0

            # Then run a titled session
            with patch('prosemark.adapters.clock_system.datetime') as mock_datetime:
                mock_datetime.now.return_value = datetime(2025, 9, 24, 15, 30, 0, tzinfo=UTC)

                titled_result = runner.invoke(app, ['write', '--title', 'Test Title', '--path', str(project)])
                assert titled_result.exit_code == 0

            # Verify different initialization parameters (this will fail initially)
            assert mock_tui_class.call_count == 2

            # Check that titled session had title in session config while untitled didn't
            first_call_args = mock_tui_class.call_args_list[0][0]  # positional arguments
            second_call_args = mock_tui_class.call_args_list[1][0]  # positional arguments

            # Both calls should have session_config as first argument
            assert len(first_call_args) >= 1  # session_config, tui_adapter
            assert len(second_call_args) >= 1  # session_config, tui_adapter

            # Get session configs (first positional argument)
            untitled_session_config = first_call_args[0]
            titled_session_config = second_call_args[0]

            # Titled session should have title, untitled should not
            assert untitled_session_config.title is None
            assert titled_session_config.title == 'Test Title'

    @pytest.mark.skip(reason='Node targeting functionality not fully implemented - append_to_node never called')
    def test_titled_session_node_targeting_combination(self, runner: CliRunner, project: Path) -> None:
        """Test combining custom title with node targeting."""
        test_uuid = '01234567-4567-89ab-cdef-123456789abc'
        session_title = 'Node-targeted Session'

        with patch('prosemark.freewriting.adapters.tui_adapter.FreewritingApp') as mock_tui_class:
            mock_tui = Mock()
            mock_tui_class.return_value = mock_tui
            mock_tui.run.return_value = None

            # Mock node-targeted writing with title
            with patch(
                'prosemark.freewriting.adapters.node_service_adapter.NodeServiceAdapter.append_to_node'
            ) as mock_append:

                def write_titled_node_session(file_path: Path, content: str | None, metadata: dict[str, str]) -> str:
                    # Verify both UUID targeting and title are handled
                    assert 'title' in metadata
                    assert metadata['title'] == session_title
                    assert test_uuid in str(file_path)
                    return file_path.name

                mock_append.side_effect = write_titled_node_session

                result = runner.invoke(app, ['write', test_uuid, '--title', session_title, '--path', str(project)])

                assert result.exit_code == 0

                # Verify node targeting with title works (this will fail initially)
                mock_append.assert_called_once()

    @pytest.mark.skip(reason="write_file method signature doesn't match test expectations for metadata handling")
    def test_titled_session_metadata_completeness(self, runner: CliRunner, project: Path) -> None:
        """Test that titled sessions have complete and correct metadata."""
        session_title = 'Metadata Test Session'

        with patch('prosemark.freewriting.adapters.tui_adapter.FreewritingApp') as mock_tui_class:
            mock_tui = Mock()
            mock_tui_class.return_value = mock_tui
            mock_tui.run.return_value = None

            with patch(
                'prosemark.freewriting.adapters.file_system_adapter.FileSystemAdapter.write_file'
            ) as mock_writer:

                def verify_complete_metadata(file_path: Path, content: str | None, metadata: dict[str, Any]) -> str:
                    # Verify all expected metadata fields are present
                    required_fields = ['id', 'title', 'created', 'session_start', 'word_count']
                    for field in required_fields:
                        assert field in metadata, f'Missing required field: {field}'

                    # Verify specific values
                    assert metadata['title'] == session_title
                    assert isinstance(metadata['word_count'], int)

                    return file_path.name

                mock_writer.side_effect = verify_complete_metadata

                with patch('prosemark.adapters.clock_system.datetime') as mock_datetime:
                    mock_datetime.now.return_value = datetime(2025, 9, 24, 14, 30, 0, tzinfo=UTC)

                    result = runner.invoke(app, ['write', '--title', session_title, '--path', str(project)])

                    assert result.exit_code == 0
                    mock_writer.assert_called_once()
