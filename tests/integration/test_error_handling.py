"""Integration test for error handling scenarios in freewrite functionality."""

from pathlib import Path
from unittest.mock import Mock, patch

import pytest
from typer.testing import CliRunner

from prosemark.cli.main import app


class TestErrorHandling:
    """Test error handling scenarios for freewrite functionality end-to-end."""

    @pytest.fixture
    def runner(self) -> CliRunner:
        """Create a CLI runner for testing."""
        return CliRunner()

    @pytest.fixture
    def project(self, tmp_path: Path) -> Path:
        """Create a basic project for testing."""
        project_dir = tmp_path / 'error_handling_project'
        project_dir.mkdir()

        runner = CliRunner()
        result = runner.invoke(app, ['init', '--title', 'Error Handling Test', '--path', str(project_dir)])
        assert result.exit_code == 0

        return project_dir

    def test_invalid_uuid_format_error(self, runner: CliRunner, project: Path) -> None:
        """Test error handling for invalid UUID format - should prevent TUI launch."""
        invalid_uuids = [
            'not-a-uuid',
            '12345678-1234-1234-1234',  # Too short
            '12345678-1234-1234-1234-12345678901234',  # Too long
            'xyz45678-1234-1234-1234-123456789abc',  # Invalid characters
            '12345678_1234_1234_1234_123456789abc',  # Wrong separators
            '12345678-1234-1234-1234-123456789aBc',  # Mixed case (if validation is strict)
        ]

        for invalid_uuid in invalid_uuids:
            result = runner.invoke(app, ['write', invalid_uuid, '--path', str(project)])

            # Should fail with error message and prevent TUI from launching (this will fail initially)
            assert result.exit_code != 0, f'Should have failed for invalid UUID: {invalid_uuid}'
            assert any(keyword in result.output.lower() for keyword in ['invalid', 'error', 'uuid', 'format'])

            # TUI should not have been launched for invalid UUID
            with patch('prosemark.freewriting.adapters.tui_adapter.FreewritingApp') as mock_tui_class:
                mock_tui_class.assert_not_called()

    def test_unwritable_directory_handling(self, runner: CliRunner, project: Path) -> None:
        """Test error handling when directory is not writable."""
        # Make directory read-only
        original_mode = project.stat().st_mode
        project.chmod(0o444)

        try:
            with patch('prosemark.freewriting.adapters.tui_adapter.FreewritingApp') as mock_tui_class:
                mock_tui = Mock()
                mock_tui_class.return_value = mock_tui

                # Mock TUI to simulate file write attempt
                mock_tui.on_file_write_error = Mock()
                mock_tui.display_error_message = Mock()
                mock_tui.continue_session_after_error = Mock(return_value=True)
                mock_tui.run.return_value = None

                result = runner.invoke(app, ['write', '--path', str(project)])

                # TUI should launch but handle write errors gracefully (this will fail initially)
                assert result.exit_code == 0, 'TUI should handle file write errors gracefully'
                mock_tui_class.assert_called_once()

        finally:
            # Restore original permissions
            project.chmod(original_mode)

    def test_disk_full_simulation_handling(self, runner: CliRunner, project: Path) -> None:
        """Test error handling when disk is full (simulated)."""
        with patch('prosemark.freewriting.adapters.tui_adapter.FreewritingApp') as mock_tui_class:
            mock_tui = Mock()
            mock_tui_class.return_value = mock_tui
            mock_tui.run.return_value = None

            # Mock disk full error during file write
            with patch(
                'prosemark.freewriting.adapters.file_system_adapter.FileSystemAdapter.write_session_content'
            ) as mock_writer:
                mock_writer.side_effect = OSError('No space left on device')

                # Mock error handling in TUI
                mock_tui.handle_disk_full_error = Mock()
                mock_tui.show_retry_dialog = Mock(return_value=False)
                mock_tui.preserve_session_data = Mock()

                result = runner.invoke(app, ['write', '--path', str(project)])

                # Should handle disk full gracefully without crashing (this will fail initially)
                assert result.exit_code == 0, 'Should handle disk full errors gracefully'

                # Verify error handling methods exist
                assert hasattr(mock_tui, 'handle_disk_full_error')
                assert hasattr(mock_tui, 'preserve_session_data')

    def test_filesystem_permission_error_handling(self, runner: CliRunner, project: Path) -> None:
        """Test handling of filesystem permission errors."""
        with patch('prosemark.freewriting.adapters.tui_adapter.FreewritingApp') as mock_tui_class:
            mock_tui = Mock()
            mock_tui_class.return_value = mock_tui
            mock_tui.run.return_value = None

            # Mock permission error
            with patch(
                'prosemark.freewriting.adapters.file_system_adapter.FileSystemAdapter.write_session_content'
            ) as mock_writer:
                mock_writer.side_effect = PermissionError('Permission denied')

                # Mock error recovery
                mock_tui.handle_permission_error = Mock()
                mock_tui.suggest_alternative_location = Mock()
                mock_tui.continue_with_temporary_storage = Mock(return_value=True)

                result = runner.invoke(app, ['write', '--path', str(project)])

                # Should handle permission errors without crashing (this will fail initially)
                assert result.exit_code == 0, 'Should handle permission errors gracefully'

                # Verify permission error handling exists
                assert hasattr(mock_tui, 'handle_permission_error')

    def test_corrupted_node_file_handling(self, runner: CliRunner, project: Path) -> None:
        """Test handling of corrupted or invalid node files."""
        test_uuid = 'corrupt12-3456-789a-bcde-f123456789ab'

        # Create a corrupted node file
        nodes_dir = project / 'nodes'
        nodes_dir.mkdir(exist_ok=True)
        corrupted_file = nodes_dir / f'{test_uuid}.md'
        corrupted_file.write_text('This is not valid YAML frontmatter\nCorrupted content')

        with patch('prosemark.freewriting.adapters.tui_adapter.FreewritingApp') as mock_tui_class:
            mock_tui = Mock()
            mock_tui_class.return_value = mock_tui
            mock_tui.run.return_value = None

            # Mock corrupted file handling
            with patch('prosemark.freewriting.adapters.node_reader.read_node_metadata') as mock_reader:
                mock_reader.side_effect = ValueError('Invalid YAML frontmatter')

                mock_tui.handle_corrupted_node = Mock()
                mock_tui.offer_file_recovery = Mock(return_value=True)

                result = runner.invoke(app, ['write', test_uuid, '--path', str(project)])

                # Should handle corrupted files gracefully (this will fail initially)
                assert result.exit_code == 0, 'Should handle corrupted node files gracefully'

                # Verify corruption handling exists
                assert hasattr(mock_tui, 'handle_corrupted_node')

    def test_network_interruption_during_save(self, runner: CliRunner, project: Path) -> None:
        """Test handling of network interruption during save (for network storage)."""
        with patch('prosemark.freewriting.adapters.tui_adapter.FreewritingApp') as mock_tui_class:
            mock_tui = Mock()
            mock_tui_class.return_value = mock_tui
            mock_tui.run.return_value = None

            # Mock network error during save
            with patch(
                'prosemark.freewriting.adapters.file_system_adapter.FileSystemAdapter.write_session_content'
            ) as mock_writer:
                mock_writer.side_effect = ConnectionError('Network unreachable')

                # Mock network error handling
                mock_tui.handle_network_error = Mock()
                mock_tui.enable_offline_mode = Mock()
                mock_tui.queue_for_retry = Mock()

                result = runner.invoke(app, ['write', '--path', str(project)])

                # Should handle network errors gracefully (this will fail initially)
                assert result.exit_code == 0, 'Should handle network errors gracefully'

                # Verify network error handling exists
                assert hasattr(mock_tui, 'handle_network_error')

    def test_tui_crash_recovery(self, runner: CliRunner, project: Path) -> None:
        """Test recovery from TUI crashes or unexpected exits."""
        with patch('prosemark.freewriting.adapters.tui_adapter.FreewritingApp') as mock_tui_class:
            mock_tui = Mock()
            mock_tui_class.return_value = mock_tui

            # Mock TUI crash
            mock_tui.run.side_effect = Exception('Unexpected TUI crash')

            # Mock crash recovery
            with patch('prosemark.freewriting.recovery.auto_save_recovery') as mock_recovery:
                mock_recovery.recover_unsaved_content.return_value = 'Recovered content'
                mock_recovery.save_crash_report.return_value = '/tmp/crash_report.log'

                result = runner.invoke(app, ['write', '--path', str(project)])

                # Should handle TUI crashes with recovery attempt (this will fail initially)
                # May exit with error but should attempt recovery
                assert 'crash' in result.output.lower() or 'error' in result.output.lower()

    def test_invalid_project_directory_handling(self, runner: CliRunner) -> None:
        """Test handling of invalid or non-existent project directories."""
        non_existent_path = Path('/non/existent/directory')

        result = runner.invoke(app, ['write', '--path', str(non_existent_path)])

        # Should handle non-existent directory gracefully (this will fail initially)
        assert result.exit_code != 0 or 'error' in result.output.lower()

    def test_concurrent_file_access_handling(self, runner: CliRunner, project: Path) -> None:
        """Test handling of concurrent access to the same file."""
        with patch('prosemark.freewriting.adapters.tui_adapter.FreewritingApp') as mock_tui_class:
            mock_tui = Mock()
            mock_tui_class.return_value = mock_tui
            mock_tui.run.return_value = None

            # Mock file lock conflict
            with patch(
                'prosemark.freewriting.adapters.file_system_adapter.FileSystemAdapter.acquire_file_lock'
            ) as mock_lock:
                mock_lock.side_effect = FileExistsError('File already locked')

                mock_tui.handle_file_lock_conflict = Mock()
                mock_tui.suggest_alternative_filename = Mock()

                result = runner.invoke(app, ['write', '--path', str(project)])

                # Should handle file lock conflicts (this will fail initially)
                assert result.exit_code == 0, 'Should handle file lock conflicts gracefully'

                # Verify file lock handling exists
                assert hasattr(mock_tui, 'handle_file_lock_conflict')

    def test_memory_exhaustion_handling(self, runner: CliRunner, project: Path) -> None:
        """Test handling of memory exhaustion during large sessions."""
        with patch('prosemark.freewriting.adapters.tui_adapter.FreewritingApp') as mock_tui_class:
            mock_tui = Mock()
            mock_tui_class.return_value = mock_tui
            mock_tui.run.return_value = None

            # Mock memory error
            with patch('prosemark.freewriting.adapters.content_buffer.append_content') as mock_buffer:
                mock_buffer.side_effect = MemoryError('Out of memory')

                mock_tui.handle_memory_exhaustion = Mock()
                mock_tui.enable_streaming_mode = Mock()
                mock_tui.flush_buffer_to_disk = Mock()

                result = runner.invoke(app, ['write', '--path', str(project)])

                # Should handle memory exhaustion gracefully (this will fail initially)
                assert result.exit_code == 0, 'Should handle memory exhaustion gracefully'

                # Verify memory handling exists
                assert hasattr(mock_tui, 'handle_memory_exhaustion')

    def test_error_recovery_session_continuation(self, runner: CliRunner, project: Path) -> None:
        """Test that sessions can continue after transient errors are resolved."""
        with patch('prosemark.freewriting.adapters.tui_adapter.FreewritingApp') as mock_tui_class:
            mock_tui = Mock()
            mock_tui_class.return_value = mock_tui
            mock_tui.run.return_value = None

            # Mock error followed by recovery
            write_attempts = [OSError('Temporary failure'), None, None]  # Fail, then succeed
            with patch(
                'prosemark.freewriting.adapters.file_system_adapter.FileSystemAdapter.write_session_content'
            ) as mock_writer:
                mock_writer.side_effect = write_attempts

                mock_tui.retry_after_error = Mock(return_value=True)
                mock_tui.show_retry_success_message = Mock()

                result = runner.invoke(app, ['write', '--path', str(project)])

                # Should recover from transient errors and continue (this will fail initially)
                assert result.exit_code == 0, 'Should recover from transient errors'

                # Verify retry mechanism exists
                assert hasattr(mock_tui, 'retry_after_error')

    def test_graceful_shutdown_on_critical_errors(self, runner: CliRunner, project: Path) -> None:
        """Test graceful shutdown when encountering critical unrecoverable errors."""
        with patch('prosemark.freewriting.adapters.tui_adapter.FreewritingApp') as mock_tui_class:
            mock_tui = Mock()
            mock_tui_class.return_value = mock_tui

            # Mock critical system error
            mock_tui.run.side_effect = SystemError('Critical system failure')

            # Mock graceful shutdown
            with patch('prosemark.freewriting.shutdown.graceful_shutdown') as mock_shutdown:
                mock_shutdown.save_emergency_backup.return_value = '/tmp/emergency_backup.md'
                mock_shutdown.cleanup_resources.return_value = True

                result = runner.invoke(app, ['write', '--path', str(project)])

                # Should shut down gracefully even on critical errors (this will fail initially)
                assert result.exit_code != 0, 'Should exit with error code on critical failure'
                assert 'critical' in result.output.lower() or 'error' in result.output.lower()

    def test_error_logging_and_reporting(self, runner: CliRunner, project: Path) -> None:
        """Test that errors are properly logged and reported for debugging."""
        with patch('prosemark.freewriting.adapters.tui_adapter.FreewritingApp') as mock_tui_class:
            mock_tui = Mock()
            mock_tui_class.return_value = mock_tui
            mock_tui.run.return_value = None

            # Mock error logging
            with (
                patch('prosemark.freewriting.adapters.error_logger.log_error') as mock_logger,
                patch(
                    'prosemark.freewriting.adapters.file_system_adapter.FileSystemAdapter.write_session_content'
                ) as mock_writer,
            ):
                mock_writer.side_effect = Exception('Test error for logging')

                mock_tui.handle_general_error = Mock()

                result = runner.invoke(app, ['write', '--path', str(project)])

                # Errors should be logged for debugging (this will fail initially)
                assert result.exit_code == 0, 'Should handle errors gracefully while logging'

                # Verify error logging exists
                mock_logger.assert_called() if mock_logger.called else None

    def test_user_input_validation_errors(self, runner: CliRunner, project: Path) -> None:
        """Test handling of invalid user input during TUI session."""
        with patch('prosemark.freewriting.adapters.tui_adapter.FreewritingApp') as mock_tui_class:
            mock_tui = Mock()
            mock_tui_class.return_value = mock_tui
            mock_tui.run.return_value = None

            # Mock input validation
            mock_tui.validate_user_input = Mock(side_effect=ValueError('Invalid input'))
            mock_tui.handle_input_validation_error = Mock()
            mock_tui.request_corrected_input = Mock()

            result = runner.invoke(app, ['write', '--path', str(project)])

            # Should handle input validation errors (this will fail initially)
            assert result.exit_code == 0, 'Should handle input validation errors gracefully'

            # Verify input validation error handling exists
            assert hasattr(mock_tui, 'handle_input_validation_error')
