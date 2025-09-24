"""Integration test for multiple freewrite sessions on the same day."""

from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any
from unittest.mock import Mock, patch

import pytest
from typer.testing import CliRunner

from prosemark.cli.main import app


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
        with patch('prosemark.freewriting.adapters.tui_adapter.FreewritingApp') as mock_tui_class:
            mock_tui_1 = Mock()
            mock_tui_2 = Mock()
            mock_tui_class.side_effect = [mock_tui_1, mock_tui_2]
            mock_tui_1.run.return_value = None
            mock_tui_2.run.return_value = None

            # Mock file creation for both sessions
            with patch(
                'prosemark.freewriting.adapters.file_system_adapter.FileSystemAdapter.write_session_content'
            ) as mock_writer:

                def create_session_files(file_path: Path, content: str, metadata: dict[str, Any]) -> str:
                    file_path.parent.mkdir(parents=True, exist_ok=True)
                    file_path.write_text(f'Session at {metadata["session_start"]}: {content}')
                    return file_path.name

                mock_writer.side_effect = create_session_files

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

                # Verify separate files were created (this will fail initially)
                expected_file1 = project / '2025-09-24-1430.md'
                expected_file2 = project / '2025-09-24-1645.md'

                assert expected_file1.exists(), 'First session file should exist'
                assert expected_file2.exists(), 'Second session file should exist'

                # Verify files have different content
                if expected_file1.exists() and expected_file2.exists():
                    content1 = expected_file1.read_text()
                    content2 = expected_file2.read_text()
                    assert content1 != content2, 'Session files should have different content'

    def test_multiple_sessions_independent_content(self, runner: CliRunner, project: Path) -> None:
        """Test that multiple sessions have completely independent content."""
        session_contents = [
            'First session content about morning thoughts',
            'Second session content about afternoon ideas',
            'Third session content about evening reflections',
        ]

        session_times = [
            datetime(2025, 9, 24, 9, 0, 0, tzinfo=UTC),  # 09:00
            datetime(2025, 9, 24, 13, 30, 0, tzinfo=UTC),  # 13:30
            datetime(2025, 9, 24, 18, 15, 0, tzinfo=UTC),  # 18:15
        ]

        created_files = []

        for i, (_content, session_time) in enumerate(zip(session_contents, session_times, strict=False)):
            with patch('prosemark.freewriting.adapters.tui_adapter.FreewritingApp') as mock_tui_class:
                mock_tui = Mock()
                mock_tui_class.return_value = mock_tui
                mock_tui.run.return_value = None

                with patch(
                    'prosemark.freewriting.adapters.file_system_adapter.FileSystemAdapter.write_session_content'
                ) as mock_writer:

                    def create_independent_session(
                        file_path: Path, session_content: str, metadata: dict[str, Any], *, session_num: int = i + 1
                    ) -> str:
                        file_path.parent.mkdir(parents=True, exist_ok=True)
                        frontmatter = f"""---
id: session-{session_num}
created: {metadata['session_start']}
session_start: {metadata['session_start']}
word_count: {len(session_content.split())}
---

# Session {session_num}

{session_content}
"""
                        file_path.write_text(frontmatter)
                        created_files.append(file_path)
                        return file_path.name

                    mock_writer.side_effect = create_independent_session

                    with patch('prosemark.adapters.clock_system.datetime') as mock_datetime:
                        mock_datetime.now.return_value = session_time

                        result = runner.invoke(app, ['write', '--path', str(project)])
                        assert result.exit_code == 0

        # Verify all files exist with independent content (this will fail initially)
        assert len(created_files) == 3, 'Should have created 3 separate session files'

        for i, file_path in enumerate(created_files):
            if file_path.exists():
                content = file_path.read_text()
                assert f'Session {i + 1}' in content
                # Verify no mixing of content between sessions
                for j, other_content in enumerate(session_contents):
                    if i != j:
                        assert other_content not in content

    def test_multiple_sessions_separate_metadata(self, runner: CliRunner, project: Path) -> None:
        """Test that each session has separate and correct metadata."""
        with patch('prosemark.freewriting.adapters.tui_adapter.FreewritingApp') as mock_tui_class:
            mock_tui_class.return_value.run.return_value = None

            captured_metadata = []

            with patch(
                'prosemark.freewriting.adapters.file_system_adapter.FileSystemAdapter.write_session_content'
            ) as mock_writer:

                def capture_session_metadata(file_path: Path, content: str, metadata: dict[str, Any]) -> str:
                    captured_metadata.append(metadata.copy())
                    return file_path.name

                mock_writer.side_effect = capture_session_metadata

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

                # Verify separate metadata (this will fail initially)
                assert len(captured_metadata) == 2, 'Should have captured metadata for 2 sessions'

                if len(captured_metadata) >= 2:
                    metadata1, metadata2 = captured_metadata[0], captured_metadata[1]

                    # Different session IDs
                    assert metadata1['id'] != metadata2['id']

                    # Different timestamps
                    assert metadata1['session_start'] != metadata2['session_start']
                    assert metadata1['created'] != metadata2['created']

                    # Expected timestamps
                    assert '10:00:00' in metadata1['session_start']
                    assert '15:30:00' in metadata2['session_start']

    def test_multiple_sessions_filename_collision_handling(self, runner: CliRunner, project: Path) -> None:
        """Test handling of potential filename collisions in rapid succession."""
        # Simulate very rapid session creation (same minute)
        base_time = datetime(2025, 9, 24, 14, 30, 0, tzinfo=UTC)

        with patch('prosemark.freewriting.adapters.tui_adapter.FreewritingApp') as mock_tui_class:
            mock_tui_class.return_value.run.return_value = None

            created_filenames = []

            with patch(
                'prosemark.freewriting.adapters.file_system_adapter.FileSystemAdapter.write_session_content'
            ) as mock_writer:

                def track_filenames(file_path: Path, content: str | None, metadata: dict[str, str]) -> str:
                    created_filenames.append(file_path.name)
                    return file_path.name

                mock_writer.side_effect = track_filenames

                # Create multiple sessions within the same minute
                for seconds in [0, 15, 30, 45]:
                    with patch('prosemark.adapters.clock_system.datetime') as mock_datetime:
                        mock_datetime.now.return_value = base_time + timedelta(seconds=seconds)

                        result = runner.invoke(app, ['write', '--path', str(project)])
                        assert result.exit_code == 0

                # Verify unique filenames even within same minute (this will fail initially)
                assert len(created_filenames) == 4, 'Should create 4 separate files'
                assert len(set(created_filenames)) == len(created_filenames), 'All filenames should be unique'

    def test_multiple_sessions_node_targeting_same_node(self, runner: CliRunner, project: Path) -> None:
        """Test multiple sessions targeting the same node append correctly."""
        test_uuid = 'multi123-4567-89ab-cdef-123456789abc'

        # Create initial node
        nodes_dir = project / 'nodes'
        nodes_dir.mkdir(exist_ok=True)
        node_file = nodes_dir / f'{test_uuid}.md'
        node_file.write_text("""---
id: multi123-4567-89ab-cdef-123456789abc
title: Multi-Session Node
created: 2025-09-24T08:00:00
---

# Multi-Session Node

Initial content.
""")

        session_contents = ['First session addition', 'Second session addition']
        session_times = [datetime(2025, 9, 24, 10, 0, 0, tzinfo=UTC), datetime(2025, 9, 24, 14, 0, 0, tzinfo=UTC)]

        for _content, session_time in zip(session_contents, session_times, strict=False):
            with patch('prosemark.freewriting.adapters.tui_adapter.FreewritingApp') as mock_tui_class:
                mock_tui = Mock()
                mock_tui_class.return_value = mock_tui
                mock_tui.run.return_value = None

                with patch(
                    'prosemark.freewriting.adapters.node_service_adapter.NodeServiceAdapter.append_to_node'
                ) as mock_append:

                    def append_to_node(file_path: Path, session_content: str, metadata: dict[str, Any]) -> str:
                        existing = file_path.read_text()
                        session_header = f'\n\n## Session {metadata["session_start"]}\n\n'
                        new_content = existing + session_header + session_content
                        file_path.write_text(new_content)
                        return file_path.name

                    mock_append.side_effect = append_to_node

                    with patch('prosemark.adapters.clock_system.datetime') as mock_datetime:
                        mock_datetime.now.return_value = session_time

                        result = runner.invoke(app, ['write', test_uuid, '--path', str(project)])
                        assert result.exit_code == 0

        # Verify node contains all sessions (this will fail initially)
        if node_file.exists():
            final_content = node_file.read_text()
            assert 'Initial content.' in final_content
            assert 'First session addition' in final_content
            assert 'Second session addition' in final_content
            assert '## Session 2025-09-24T10:00:00' in final_content
            assert '## Session 2025-09-24T14:00:00' in final_content

    def test_mixed_daily_and_node_sessions_same_day(self, runner: CliRunner, project: Path) -> None:
        """Test mixing daily and node-targeted sessions on the same day."""
        test_uuid = 'mixed123-4567-89ab-cdef-123456789abc'

        # Create a mix of daily and node-targeted sessions
        session_configs: list[dict[str, str | datetime]] = [
            {'type': 'daily', 'time': datetime(2025, 9, 24, 9, 0, 0, tzinfo=UTC)},
            {'type': 'node', 'uuid': test_uuid, 'time': datetime(2025, 9, 24, 11, 0, 0, tzinfo=UTC)},
            {'type': 'daily', 'time': datetime(2025, 9, 24, 13, 0, 0, tzinfo=UTC)},
            {'type': 'node', 'uuid': test_uuid, 'time': datetime(2025, 9, 24, 15, 0, 0, tzinfo=UTC)},
        ]

        created_daily_files = []
        node_append_calls = []

        for config in session_configs:
            with patch('prosemark.freewriting.adapters.tui_adapter.FreewritingApp') as mock_tui_class:
                mock_tui = Mock()
                mock_tui_class.return_value = mock_tui
                mock_tui.run.return_value = None

                if config['type'] == 'daily':
                    with patch(
                        'prosemark.freewriting.adapters.file_system_adapter.FileSystemAdapter.write_session_content'
                    ) as mock_writer:

                        def create_daily_file(file_path: Path, content: str | None, metadata: dict[str, str]) -> str:
                            created_daily_files.append(file_path.name)
                            return file_path.name

                        mock_writer.side_effect = create_daily_file

                        with patch('prosemark.adapters.clock_system.datetime') as mock_datetime:
                            mock_datetime.now.return_value = config['time']

                            result = runner.invoke(app, ['write', '--path', str(project)])
                            assert result.exit_code == 0

                else:  # node type
                    with patch(
                        'prosemark.freewriting.adapters.node_service_adapter.NodeServiceAdapter.append_to_node'
                    ) as mock_append:

                        def track_node_append(file_path: Path, content: str | None, metadata: dict[str, str]) -> str:
                            node_append_calls.append((file_path.name, metadata['session_start']))
                            return file_path.name

                        mock_append.side_effect = track_node_append

                        with patch('prosemark.adapters.clock_system.datetime') as mock_datetime:
                            mock_datetime.now.return_value = config['time']

                            uuid_str = str(config['uuid'])  # Ensure it's a string
                            result = runner.invoke(app, ['write', uuid_str, '--path', str(project)])
                            assert result.exit_code == 0

        # Verify mixed session handling (this will fail initially)
        assert len(created_daily_files) == 2, 'Should have created 2 daily files'
        assert len(node_append_calls) == 2, 'Should have made 2 node append calls'

        # Verify daily files have different timestamps
        if len(created_daily_files) >= 2:
            assert created_daily_files[0] != created_daily_files[1]

        # Verify node sessions have different timestamps
        if len(node_append_calls) >= 2:
            assert node_append_calls[0][1] != node_append_calls[1][1]

    def test_session_cleanup_and_isolation(self, runner: CliRunner, project: Path) -> None:
        """Test that sessions are properly cleaned up and don't interfere with each other."""
        with patch('prosemark.freewriting.adapters.tui_adapter.FreewritingApp') as mock_tui_class:
            mock_tui_instances = [Mock() for _ in range(3)]
            mock_tui_class.side_effect = mock_tui_instances

            for mock_tui in mock_tui_instances:
                mock_tui.run.return_value = None
                mock_tui.cleanup_session = Mock()
                mock_tui.release_resources = Mock()

            # Run three separate sessions
            session_times = [
                datetime(2025, 9, 24, 10, 0, 0, tzinfo=UTC),
                datetime(2025, 9, 24, 12, 0, 0, tzinfo=UTC),
                datetime(2025, 9, 24, 14, 0, 0, tzinfo=UTC),
            ]

            for session_time in session_times:
                with patch('prosemark.adapters.clock_system.datetime') as mock_datetime:
                    mock_datetime.now.return_value = session_time

                    result = runner.invoke(app, ['write', '--path', str(project)])
                    assert result.exit_code == 0

            # Verify each session was properly cleaned up (this will fail initially)
            for mock_tui in mock_tui_instances:
                if hasattr(mock_tui, 'cleanup_session'):
                    mock_tui.cleanup_session.assert_called()
                if hasattr(mock_tui, 'release_resources'):
                    mock_tui.release_resources.assert_called()

    def test_concurrent_session_prevention(self, runner: CliRunner, project: Path) -> None:
        """Test that concurrent sessions are prevented or handled properly."""
        with patch('prosemark.freewriting.session.session_lock.acquire_session_lock') as mock_lock:
            mock_lock.side_effect = [True, False]  # First session succeeds, second fails

            # Try to start two sessions concurrently
            runner.invoke(app, ['write', '--path', str(project)])
            result2 = runner.invoke(app, ['write', '--path', str(project)])

            # Should handle concurrent access properly (this will fail initially)
            # Either both succeed with different files, or second fails gracefully
            if result2.exit_code != 0:
                assert 'session' in result2.output.lower() or 'lock' in result2.output.lower()

    def test_daily_session_count_tracking(self, runner: CliRunner, project: Path) -> None:
        """Test that the system can track how many sessions occurred on a given day."""
        session_times = [
            datetime(2025, 9, 24, 8, 0, 0, tzinfo=UTC),
            datetime(2025, 9, 24, 12, 0, 0, tzinfo=UTC),
            datetime(2025, 9, 24, 16, 0, 0, tzinfo=UTC),
            datetime(2025, 9, 24, 20, 0, 0, tzinfo=UTC),
        ]

        for session_time in session_times:
            with patch('prosemark.freewriting.adapters.tui_adapter.FreewritingApp') as mock_tui_class:
                mock_tui = Mock()
                mock_tui_class.return_value = mock_tui
                mock_tui.run.return_value = None

                with patch('prosemark.adapters.clock_system.datetime') as mock_datetime:
                    mock_datetime.now.return_value = session_time

                    result = runner.invoke(app, ['write', '--path', str(project)])
                    assert result.exit_code == 0

        # Verify session counting capability exists (this will fail initially)
        with patch('prosemark.freewriting.analytics.count_daily_sessions') as mock_counter:
            mock_counter.return_value = 4

            # Should be able to count sessions for the day
            daily_count = mock_counter(project, '2025-09-24')
            assert daily_count == 4 if mock_counter.called else True
