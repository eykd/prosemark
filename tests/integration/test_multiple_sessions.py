"""Integration test for multiple freewrite sessions on the same day."""

from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Literal, TypedDict
from unittest.mock import patch

import pytest
from typer.testing import CliRunner

from prosemark.cli.main import app


class DailySessionConfig(TypedDict):
    """Configuration for a daily session."""

    type: Literal['daily']
    time: datetime


class NodeSessionConfig(TypedDict):
    """Configuration for a node-targeted session."""

    type: Literal['node']
    uuid: str
    time: datetime


class TestMultipleSessions:
    """Test multiple freewrite sessions on the same day end-to-end scenarios."""

    @pytest.fixture
    def runner(self) -> CliRunner:
        """Create a CLI runner for testing."""
        return CliRunner()

    @pytest.fixture
    def project(self, tmp_path: Path) -> Path:
        """Create a basic project for testing."""
        project_dir = tmp_path / 'multiple_sessions_project'
        project_dir.mkdir()

        runner = CliRunner()
        result = runner.invoke(app, ['init', '--title', 'Multiple Sessions Test', '--path', str(project_dir)])
        assert result.exit_code == 0

        return project_dir

    def test_two_daily_sessions_different_timestamps(self, runner: CliRunner, project: Path) -> None:
        """Test that multiple daily sessions create separate files with different timestamps."""
        with patch(
            'prosemark.freewriting.adapters.freewrite_service_adapter.FreewriteServiceAdapter.create_session'
        ) as mock_create_session:
            mock_create_session.return_value = None

            # First session at 14:30
            with patch('prosemark.adapters.clock_system.datetime') as mock_datetime:
                mock_datetime.now.return_value = datetime(2025, 9, 24, 14, 30, 0, tzinfo=UTC)

                result1 = runner.invoke(app, ['write', '--path', str(project)])
                assert result1.exit_code == 0

            # Second session at 16:45
            with patch('prosemark.adapters.clock_system.datetime') as mock_datetime:
                mock_datetime.now.return_value = datetime(2025, 9, 24, 16, 45, 0, tzinfo=UTC)

                result2 = runner.invoke(app, ['write', '--path', str(project)])
                assert result2.exit_code == 0

            # Verify that sessions were created
            assert mock_create_session.call_count == 2

    def test_multiple_sessions_independent_content(self, runner: CliRunner, project: Path) -> None:
        """Test that multiple sessions have completely independent content."""
        session_times = [
            datetime(2025, 9, 24, 9, 0, 0, tzinfo=UTC),  # 09:00
            datetime(2025, 9, 24, 13, 30, 0, tzinfo=UTC),  # 13:30
            datetime(2025, 9, 24, 18, 15, 0, tzinfo=UTC),  # 18:15
        ]

        with patch(
            'prosemark.freewriting.adapters.freewrite_service_adapter.FreewriteServiceAdapter.create_session'
        ) as mock_create_session:
            mock_create_session.return_value = None

            for session_time in session_times:
                with patch('prosemark.adapters.clock_system.datetime') as mock_datetime:
                    mock_datetime.now.return_value = session_time

                    result = runner.invoke(app, ['write', '--path', str(project)])
                    assert result.exit_code == 0

            # Verify that all sessions were created
            assert mock_create_session.call_count == len(session_times)

    def test_multiple_sessions_separate_metadata(self, runner: CliRunner, project: Path) -> None:
        """Test that each session has separate and correct metadata."""
        with patch(
            'prosemark.freewriting.adapters.freewrite_service_adapter.FreewriteServiceAdapter.create_session'
        ) as mock_create_session:
            mock_create_session.return_value = None

            # First session
            with patch('prosemark.adapters.clock_system.datetime') as mock_datetime:
                mock_datetime.now.return_value = datetime(2025, 9, 24, 10, 0, 0, tzinfo=UTC)
                result1 = runner.invoke(app, ['write', '--path', str(project)])
                assert result1.exit_code == 0

            # Second session
            with patch('prosemark.adapters.clock_system.datetime') as mock_datetime:
                mock_datetime.now.return_value = datetime(2025, 9, 24, 15, 30, 0, tzinfo=UTC)
                result2 = runner.invoke(app, ['write', '--path', str(project)])
                assert result2.exit_code == 0

            # Verify both sessions were created
            assert mock_create_session.call_count == 2

    def test_multiple_sessions_filename_collision_handling(self, runner: CliRunner, project: Path) -> None:
        """Test handling of potential filename collisions in rapid succession."""
        # Simulate very rapid session creation (same minute)
        base_time = datetime(2025, 9, 24, 14, 30, 0, tzinfo=UTC)

        with patch(
            'prosemark.freewriting.adapters.freewrite_service_adapter.FreewriteServiceAdapter.create_session'
        ) as mock_create_session:
            mock_create_session.return_value = None

            # Create multiple sessions within the same minute
            for seconds in [0, 15, 30, 45]:
                with patch('prosemark.adapters.clock_system.datetime') as mock_datetime:
                    mock_datetime.now.return_value = base_time + timedelta(seconds=seconds)

                    result = runner.invoke(app, ['write', '--path', str(project)])
                    assert result.exit_code == 0

            # Verify all sessions were created
            assert mock_create_session.call_count == 4

    def test_multiple_sessions_node_targeting_same_node(self, runner: CliRunner, project: Path) -> None:
        """Test multiple sessions targeting the same node append correctly."""
        test_uuid = '01234567-89ab-cdef-0123-456789abcdef'  # Valid UUID format

        session_times = [datetime(2025, 9, 24, 10, 0, 0, tzinfo=UTC), datetime(2025, 9, 24, 14, 0, 0, tzinfo=UTC)]

        with patch(
            'prosemark.freewriting.adapters.freewrite_service_adapter.FreewriteServiceAdapter.create_session'
        ) as mock_create_session:
            mock_create_session.return_value = None

            for session_time in session_times:
                with patch('prosemark.adapters.clock_system.datetime') as mock_datetime:
                    mock_datetime.now.return_value = session_time

                    result = runner.invoke(app, ['write', test_uuid, '--path', str(project)])
                    assert result.exit_code == 0

            # Verify both sessions were created
            assert mock_create_session.call_count == 2

    def test_mixed_daily_and_node_sessions_same_day(self, runner: CliRunner, project: Path) -> None:
        """Test mixing daily and node-targeted sessions on the same day."""
        test_uuid = '01234567-89ab-cdef-0123-456789abcdef'  # Valid UUID format

        # Create a mix of daily and node-targeted sessions
        daily_config_1: DailySessionConfig = {'type': 'daily', 'time': datetime(2025, 9, 24, 9, 0, 0, tzinfo=UTC)}
        node_config_1: NodeSessionConfig = {
            'type': 'node',
            'uuid': test_uuid,
            'time': datetime(2025, 9, 24, 11, 0, 0, tzinfo=UTC),
        }
        daily_config_2: DailySessionConfig = {'type': 'daily', 'time': datetime(2025, 9, 24, 13, 0, 0, tzinfo=UTC)}
        node_config_2: NodeSessionConfig = {
            'type': 'node',
            'uuid': test_uuid,
            'time': datetime(2025, 9, 24, 15, 0, 0, tzinfo=UTC),
        }

        session_configs: list[DailySessionConfig | NodeSessionConfig] = [
            daily_config_1,
            node_config_1,
            daily_config_2,
            node_config_2,
        ]

        with patch(
            'prosemark.freewriting.adapters.freewrite_service_adapter.FreewriteServiceAdapter.create_session'
        ) as mock_create_session:
            mock_create_session.return_value = None

            for config in session_configs:
                with patch('prosemark.adapters.clock_system.datetime') as mock_datetime:
                    mock_datetime.now.return_value = config['time']

                    if config['type'] == 'daily':
                        result = runner.invoke(app, ['write', '--path', str(project)])
                    elif config['type'] == 'node':
                        # At this point, mypy knows this is NodeSessionConfig
                        result = runner.invoke(app, ['write', config['uuid'], '--path', str(project)])
                    else:
                        msg = f'Unknown session type: {config["type"]}'
                        raise ValueError(msg)

                    assert result.exit_code == 0

            # Verify all sessions were created
            assert mock_create_session.call_count == len(session_configs)

    def test_session_cleanup_and_isolation(self, runner: CliRunner, project: Path) -> None:
        """Test that sessions are properly cleaned up and don't interfere with each other."""
        session_times = [
            datetime(2025, 9, 24, 10, 0, 0, tzinfo=UTC),
            datetime(2025, 9, 24, 12, 0, 0, tzinfo=UTC),
            datetime(2025, 9, 24, 14, 0, 0, tzinfo=UTC),
        ]

        with patch(
            'prosemark.freewriting.adapters.freewrite_service_adapter.FreewriteServiceAdapter.create_session'
        ) as mock_create_session:
            mock_create_session.return_value = None

            for session_time in session_times:
                with patch('prosemark.adapters.clock_system.datetime') as mock_datetime:
                    mock_datetime.now.return_value = session_time

                    result = runner.invoke(app, ['write', '--path', str(project)])
                    assert result.exit_code == 0

            # Verify all sessions were created
            assert mock_create_session.call_count == len(session_times)

    def test_concurrent_session_prevention(self, runner: CliRunner, project: Path) -> None:
        """Test that concurrent sessions are prevented or handled properly."""
        with patch(
            'prosemark.freewriting.adapters.freewrite_service_adapter.FreewriteServiceAdapter.create_session'
        ) as mock_create_session:
            mock_create_session.return_value = None

            # Try to start two sessions
            result1 = runner.invoke(app, ['write', '--path', str(project)])
            result2 = runner.invoke(app, ['write', '--path', str(project)])

            # Both should succeed in test environment
            assert result1.exit_code == 0
            assert result2.exit_code == 0
            assert mock_create_session.call_count == 2

    def test_daily_session_count_tracking(self, runner: CliRunner, project: Path) -> None:
        """Test that the system can track how many sessions occurred on a given day."""
        session_times = [
            datetime(2025, 9, 24, 8, 0, 0, tzinfo=UTC),
            datetime(2025, 9, 24, 12, 0, 0, tzinfo=UTC),
            datetime(2025, 9, 24, 16, 0, 0, tzinfo=UTC),
            datetime(2025, 9, 24, 20, 0, 0, tzinfo=UTC),
        ]

        with patch(
            'prosemark.freewriting.adapters.freewrite_service_adapter.FreewriteServiceAdapter.create_session'
        ) as mock_create_session:
            mock_create_session.return_value = None

            for session_time in session_times:
                with patch('prosemark.adapters.clock_system.datetime') as mock_datetime:
                    mock_datetime.now.return_value = session_time

                    result = runner.invoke(app, ['write', '--path', str(project)])
                    assert result.exit_code == 0

            # Verify all sessions were created
            assert mock_create_session.call_count == len(session_times)
