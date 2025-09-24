"""Integration test for node targeting freewrite functionality."""

from datetime import UTC, datetime
from pathlib import Path
from unittest.mock import Mock, patch

import pytest
from typer.testing import CliRunner

from prosemark.cli.main import app


class TestNodeFreewrite:
    """Test freewrite targeting specific nodes end-to-end scenarios."""

    @pytest.fixture
    def runner(self) -> CliRunner:
        """Create a CLI runner for testing."""
        return CliRunner()

    @pytest.fixture
    def project(self, tmp_path: Path) -> Path:
        """Create a basic project for testing."""
        project_dir = tmp_path / 'node_freewrite_project'
        project_dir.mkdir()

        runner = CliRunner()
        result = runner.invoke(app, ['init', '--title', 'Node Freewrite Test', '--path', str(project_dir)])
        assert result.exit_code == 0

        return project_dir

    @pytest.fixture
    def test_uuid(self) -> str:
        """Provide a consistent UUID for testing."""
        return '01234567-89ab-cdef-0123-456789abcdef'

    def test_freewrite_to_existing_node(self, runner: CliRunner, project: Path, test_uuid: str) -> None:
        """Test freewriting content to an existing node."""
        # First create the node
        with patch('prosemark.adapters.id_generator.SimpleIdGenerator.new') as mock_gen:
            mock_gen.return_value = test_uuid
            create_result = runner.invoke(app, ['add', 'Test Node', '--path', str(project)])
            assert create_result.exit_code == 0

        # Mock the TUI interface for freewriting to the node
        with patch('prosemark.freewriting.adapters.tui_adapter.FreewritingApp') as mock_tui_class:
            mock_tui = Mock()
            mock_tui_class.return_value = mock_tui
            mock_tui.run.return_value = None

            # Mock content appending
            with patch(
                'prosemark.freewriting.adapters.node_service_adapter.NodeServiceAdapter.append_to_node'
            ) as mock_append:
                mock_append.return_value = f'{test_uuid}.md'

                result = runner.invoke(app, ['write', test_uuid, '--path', str(project)])

                assert result.exit_code == 0

                # Verify the append function was called with correct node ID (this will fail initially)
                mock_append.assert_called_once()
                call_args = mock_append.call_args[0]
                assert test_uuid in str(call_args[0])  # file path should contain UUID

    def test_freewrite_to_new_node_auto_creation(self, runner: CliRunner, project: Path) -> None:
        """Test freewriting to a non-existing node creates it automatically."""
        new_uuid = 'fedcba98-7654-3210-fedc-ba9876543210'

        with patch('prosemark.freewriting.adapters.tui_adapter.FreewritingApp') as mock_tui_class:
            mock_tui = Mock()
            mock_tui_class.return_value = mock_tui
            mock_tui.run.return_value = None

            # Mock node creation and content writing
            with patch('prosemark.freewriting.adapters.node_creator.create_node') as mock_create:
                mock_create.return_value = Path(project) / 'nodes' / f'{new_uuid}.md'

                with patch(
                    'prosemark.freewriting.adapters.node_service_adapter.NodeServiceAdapter.append_to_node'
                ) as mock_append:
                    mock_append.return_value = f'{new_uuid}.md'

                    result = runner.invoke(app, ['write', new_uuid, '--path', str(project)])

                    assert result.exit_code == 0

                    # Verify node creation was triggered (this will fail initially)
                    mock_create.assert_called_once()

                    # Verify content was appended to the new node
                    mock_append.assert_called_once()

    def test_node_freewrite_session_header(self, runner: CliRunner, project: Path, test_uuid: str) -> None:
        """Test that node freewrite sessions include session headers."""
        # Create existing node
        with patch('prosemark.adapters.id_generator.SimpleIdGenerator.new') as mock_gen:
            mock_gen.return_value = test_uuid
            runner.invoke(app, ['add', 'Test Node', '--path', str(project)])

        with patch('prosemark.freewriting.adapters.tui_adapter.FreewritingApp') as mock_tui_class:
            mock_tui = Mock()
            mock_tui_class.return_value = mock_tui
            mock_tui.run.return_value = None

            with patch('prosemark.adapters.clock_system.datetime') as mock_datetime:
                mock_datetime.now.return_value = datetime(2025, 9, 24, 16, 45, 0, tzinfo=UTC)

                # Mock the file writing to capture session header
                with patch(
                    'prosemark.freewriting.adapters.node_service_adapter.NodeServiceAdapter.append_to_node'
                ) as mock_append:

                    def capture_session_write(
                        file_path: Path, content: str | None, session_metadata: dict[str, str]
                    ) -> str:
                        # Verify session header format
                        expected_header = f'\n\n## Session {session_metadata["session_start"]}\n\n'
                        assert (content and expected_header in content) or session_metadata[
                            'session_start'
                        ] == '2025-09-24T16:45:00'
                        return file_path.name

                    mock_append.side_effect = capture_session_write

                    result = runner.invoke(app, ['write', test_uuid, '--path', str(project)])

                    assert result.exit_code == 0
                    mock_append.assert_called_once()

    def test_node_freewrite_binder_update(self, runner: CliRunner, project: Path) -> None:
        """Test that new nodes created via freewrite are added to binder."""
        new_uuid = 'binder123-4567-89ab-cdef-123456789abc'

        with patch('prosemark.freewriting.adapters.tui_adapter.FreewritingApp') as mock_tui_class:
            mock_tui = Mock()
            mock_tui_class.return_value = mock_tui
            mock_tui.run.return_value = None

            # Mock binder update functionality
            with patch('prosemark.freewriting.adapters.binder_updater.add_node_to_binder') as mock_binder:
                mock_binder.return_value = True

                with patch('prosemark.freewriting.adapters.node_creator.create_node') as mock_create:
                    mock_create.return_value = Path(project) / 'nodes' / f'{new_uuid}.md'

                    result = runner.invoke(app, ['write', new_uuid, '--path', str(project)])

                    assert result.exit_code == 0

                    # Verify binder was updated (this will fail initially)
                    mock_binder.assert_called_once()
                    call_args = mock_binder.call_args[0]
                    assert new_uuid in str(call_args[0])

    def test_node_freewrite_content_appending(self, runner: CliRunner, project: Path, test_uuid: str) -> None:
        """Test that content is properly appended to existing node content."""
        # Create node with initial content
        node_file = project / 'nodes' / f'{test_uuid}.md'
        node_file.parent.mkdir(parents=True, exist_ok=True)

        initial_content = f"""---
id: {test_uuid}
title: Test Node
created: 2025-09-24T10:00:00
---

# Test Node

Initial content here.
"""
        node_file.write_text(initial_content)

        with patch('prosemark.freewriting.adapters.tui_adapter.FreewritingApp') as mock_tui_class:
            mock_tui = Mock()
            mock_tui_class.return_value = mock_tui
            mock_tui.run.return_value = None

            # Mock content capture and writing
            with patch(
                'prosemark.freewriting.adapters.node_service_adapter.NodeServiceAdapter.append_to_node'
            ) as mock_append:

                def write_appended_content(file_path: Path, content: str | None, metadata: dict[str, str]) -> str:
                    # Simulate appending to existing file
                    existing = file_path.read_text()
                    session_header = f'\n\n## Session {metadata["session_start"]}\n\n'
                    new_content = existing + session_header + (content or '')
                    file_path.write_text(new_content)
                    return file_path.name

                mock_append.side_effect = write_appended_content

                with patch('prosemark.adapters.clock_system.datetime') as mock_datetime:
                    mock_datetime.now.return_value = datetime(2025, 9, 24, 16, 45, 0, tzinfo=UTC)

                    result = runner.invoke(app, ['write', test_uuid, '--path', str(project)])

                    assert result.exit_code == 0

                    # This test will fail initially as the append functionality doesn't exist
                    if node_file.exists():
                        final_content = node_file.read_text()
                        assert 'Initial content here.' in final_content
                        assert '## Session 2025-09-24T16:45:00' in final_content

    def test_invalid_uuid_format_error(self, runner: CliRunner, project: Path) -> None:
        """Test error handling for invalid UUID format."""
        invalid_uuids = [
            'not-a-uuid',
            '12345678-1234-1234-1234',  # Too short
            '12345678-1234-1234-1234-12345678901234',  # Too long
            'xyz45678-1234-1234-1234-123456789abc',  # Invalid characters
        ]

        for invalid_uuid in invalid_uuids:
            result = runner.invoke(app, ['write', invalid_uuid, '--path', str(project)])

            # Should fail with error message (this will fail initially as validation doesn't exist)
            assert result.exit_code != 0, f'Should have failed for invalid UUID: {invalid_uuid}'
            assert 'invalid' in result.output.lower() or 'error' in result.output.lower()

    def test_node_freewrite_yaml_frontmatter_preservation(
        self, runner: CliRunner, project: Path, test_uuid: str
    ) -> None:
        """Test that existing node YAML frontmatter is preserved when appending."""
        # Create node with complex frontmatter
        node_file = project / 'nodes' / f'{test_uuid}.md'
        node_file.parent.mkdir(parents=True, exist_ok=True)

        initial_content = f"""---
id: {test_uuid}
title: Complex Node
created: 2025-09-24T10:00:00
tags:
  - important
  - draft
metadata:
  author: test-user
  version: 1.0
---

# Complex Node

Original content.
"""
        node_file.write_text(initial_content)

        with patch('prosemark.freewriting.adapters.tui_adapter.FreewritingApp') as mock_tui_class:
            mock_tui = Mock()
            mock_tui_class.return_value = mock_tui
            mock_tui.run.return_value = None

            with patch(
                'prosemark.freewriting.adapters.node_service_adapter.NodeServiceAdapter.append_to_node'
            ) as mock_append:

                def preserve_frontmatter(file_path: Path, content: str | None, metadata: dict[str, str]) -> str:
                    # This should preserve the existing frontmatter
                    existing = file_path.read_text()
                    # Find end of frontmatter
                    parts = existing.split('---', 2)
                    if len(parts) >= 3:
                        frontmatter = f'---{parts[1]}---'
                        body = parts[2]
                        session_header = f'\n\n## Session {metadata["session_start"]}\n\n'
                        new_content = frontmatter + body + session_header + (content or '')
                        file_path.write_text(new_content)
                    return file_path.name

                mock_append.side_effect = preserve_frontmatter

                result = runner.invoke(app, ['write', test_uuid, '--path', str(project)])

                assert result.exit_code == 0

                # Verify frontmatter preservation (this will fail initially)
                if node_file.exists():
                    final_content = node_file.read_text()
                    assert 'tags:' in final_content
                    assert '- important' in final_content
                    assert 'author: test-user' in final_content
                    assert 'version: 1.0' in final_content

    def test_node_freewrite_directory_structure(self, runner: CliRunner, project: Path) -> None:
        """Test that node freewrite respects prosemark directory conventions."""
        new_uuid = 'struct12-3456-789a-bcde-f123456789ab'

        with patch('prosemark.freewriting.adapters.tui_adapter.FreewritingApp') as mock_tui_class:
            mock_tui = Mock()
            mock_tui_class.return_value = mock_tui
            mock_tui.run.return_value = None

            # Mock node creation with proper directory structure
            with patch('prosemark.freewriting.adapters.node_creator.create_node') as mock_create:
                expected_path = project / 'nodes' / f'{new_uuid}.md'
                mock_create.return_value = expected_path

                result = runner.invoke(app, ['write', new_uuid, '--path', str(project)])

                assert result.exit_code == 0

                # Verify correct directory structure is used (this will fail initially)
                mock_create.assert_called_once()
                call_args = mock_create.call_args[0]
                # Should be creating in nodes/ directory
                assert 'nodes' in str(call_args[0]) or call_args[0] == expected_path
