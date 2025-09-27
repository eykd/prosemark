"""Simplified tests for main CLI module to achieve coverage."""

import json
from pathlib import Path
from typing import NamedTuple
from unittest.mock import Mock, patch

from typer.testing import CliRunner

from prosemark.cli.main import (
    FileSystemConfigPort,
    _get_project_root,
    app,
)
from prosemark.domain.models import NodeId
from prosemark.exceptions import (
    BinderIntegrityError,
    EditorLaunchError,
    FileSystemError,
    NodeNotFoundError,
    PlaceholderNotFoundError,
)


class MaterializeResult(NamedTuple):
    node_id: NodeId
    was_already_materialized: bool


class TestSimpleMainFunctions:
    """Simple tests to cover main CLI functions."""

    def test_get_project_root_returns_current_directory(self) -> None:
        """Test that _get_project_root returns current working directory."""
        result = _get_project_root()
        assert result == Path.cwd()

    def test_filesystem_config_port_methods(self) -> None:
        """Test all FileSystemConfigPort methods."""
        config_port = FileSystemConfigPort()
        test_path = Path('/test/config.yaml')

        # Test create_default_config (should do nothing)
        config_port.create_default_config(test_path)

        # Test config_exists with non-existent path
        assert config_port.config_exists(test_path) is False

        # Test get_default_config_values
        assert config_port.get_default_config_values() == {}

        # Test load_config
        assert config_port.load_config(test_path) == {}


class TestMainAppIntegration:
    """Integration tests for the main Typer app."""

    def setup_method(self) -> None:
        """Set up test environment."""
        self.runner = CliRunner()

    @patch('prosemark.cli.main.InitProject')
    @patch('prosemark.cli.main.BinderRepoFs')
    @patch('prosemark.cli.main.ConsolePretty')
    @patch('prosemark.cli.main.LoggerStdout')
    @patch('prosemark.cli.main.ClockSystem')
    def test_init_command_success_integration(
        self,
        mock_clock: Mock,
        mock_logger: Mock,
        mock_console: Mock,
        mock_binder_repo: Mock,
        mock_init_project: Mock,
    ) -> None:
        """Test successful init command integration."""
        mock_interactor = Mock()
        mock_init_project.return_value = mock_interactor

        result = self.runner.invoke(app, ['init', '--title', 'Test Project'])

        assert result.exit_code == 0
        assert 'Project "Test Project" initialized successfully' in result.stdout
        assert 'Created _binder.md with project structure' in result.stdout
        mock_interactor.execute.assert_called_once()

    @patch('prosemark.cli.main.InitProject')
    @patch('prosemark.cli.main.BinderRepoFs')
    def test_init_command_binder_integrity_error(
        self,
        mock_binder_repo: Mock,
        mock_init_project: Mock,
    ) -> None:
        """Test init command with existing project error."""
        mock_interactor = Mock()
        mock_init_project.return_value = mock_interactor
        mock_interactor.execute.side_effect = BinderIntegrityError('Already exists')

        result = self.runner.invoke(app, ['init', '--title', 'Test Project'])

        assert result.exit_code == 1
        assert 'Error: Directory already contains a prosemark project' in result.stdout

    @patch('prosemark.cli.main.InitProject')
    @patch('prosemark.cli.main.BinderRepoFs')
    def test_init_command_filesystem_error(
        self,
        mock_binder_repo: Mock,
        mock_init_project: Mock,
    ) -> None:
        """Test init command with filesystem error."""
        mock_interactor = Mock()
        mock_init_project.return_value = mock_interactor
        mock_interactor.execute.side_effect = FileSystemError('Permission denied')

        result = self.runner.invoke(app, ['init', '--title', 'Test Project'])

        assert result.exit_code == 2
        assert 'Error: Permission denied' in result.stdout

    @patch('prosemark.cli.main.InitProject')
    @patch('prosemark.cli.main.BinderRepoFs')
    def test_init_command_unexpected_error(
        self,
        mock_binder_repo: Mock,
        mock_init_project: Mock,
    ) -> None:
        """Test init command with unexpected error."""
        mock_interactor = Mock()
        mock_init_project.return_value = mock_interactor
        mock_interactor.execute.side_effect = Exception('Unexpected error')

        result = self.runner.invoke(app, ['init', '--title', 'Test Project'])

        assert result.exit_code == 3
        assert 'Unexpected error: Unexpected error' in result.stdout

    @patch('prosemark.cli.main.AddNode')
    @patch('prosemark.cli.main._get_project_root')
    @patch('prosemark.cli.main.BinderRepoFs')
    @patch('prosemark.cli.main.NodeRepoFs')
    @patch('prosemark.cli.main.IdGeneratorUuid7')
    def test_add_command_success(
        self,
        mock_id_gen: Mock,
        mock_node_repo: Mock,
        mock_binder_repo: Mock,
        mock_get_root: Mock,
        mock_add_node: Mock,
    ) -> None:
        """Test successful add command."""
        valid_node_id = str(NodeId.generate())
        mock_get_root.return_value = Path('/test')
        mock_interactor = Mock()
        mock_add_node.return_value = mock_interactor
        mock_interactor.execute.return_value = valid_node_id

        result = self.runner.invoke(app, ['add', 'Test Node'])

        assert result.exit_code == 0
        assert f'Added "Test Node" ({valid_node_id})' in result.stdout

    @patch('prosemark.cli.main.run_freewriting_session')
    def test_write_command_success(self, mock_run_freewriting: Mock, tmp_path: Path) -> None:
        """Test successful write command."""
        mock_run_freewriting.return_value = None

        result = self.runner.invoke(app, ['write', '--title', 'Test Title', '--path', str(tmp_path)])

        assert result.exit_code == 0
        mock_run_freewriting.assert_called_once_with(
            node_uuid=None,
            title='Test Title',
            word_count_goal=None,
            time_limit=None,
            project_path=tmp_path,
        )

    @patch('prosemark.cli.main.run_freewriting_session')
    def test_write_command_filesystem_error(self, mock_run_freewriting: Mock, tmp_path: Path) -> None:
        """Test write command with filesystem error."""
        mock_run_freewriting.side_effect = FileSystemError('Disk full')

        result = self.runner.invoke(app, ['write', '--path', str(tmp_path)])

        # Check if the mock was called
        mock_run_freewriting.assert_called_once()
        assert result.exit_code == 1
        assert 'Disk full' in result.stdout

    @patch('prosemark.cli.main.run_freewriting_session')
    def test_write_command_editor_launch_error(self, mock_run_freewriting: Mock, tmp_path: Path) -> None:
        """Test write command with editor launch error."""
        mock_run_freewriting.side_effect = EditorLaunchError('No editor')

        result = self.runner.invoke(app, ['write', '--path', str(tmp_path)])

        assert result.exit_code == 1  # All exceptions result in exit code 1
        assert 'No editor' in result.stdout

    @patch('prosemark.cli.main.ShowStructure')
    @patch('prosemark.cli.main._get_project_root')
    @patch('prosemark.cli.main.BinderRepoFs')
    def test_structure_command_tree_format(
        self,
        mock_binder_repo: Mock,
        mock_get_root: Mock,
        mock_show_structure: Mock,
    ) -> None:
        """Test structure command with tree format."""
        mock_get_root.return_value = Path('/test')
        mock_interactor = Mock()
        mock_show_structure.return_value = mock_interactor
        mock_interactor.execute.return_value = 'Project Tree'

        result = self.runner.invoke(app, ['structure'])

        assert result.exit_code == 0
        assert 'Project Structure:' in result.stdout
        assert 'Project Tree' in result.stdout

    @patch('prosemark.cli.main.ShowStructure')
    @patch('prosemark.cli.main._get_project_root')
    @patch('prosemark.cli.main.BinderRepoFs')
    def test_structure_command_json_format(
        self,
        mock_binder_repo: Mock,
        mock_get_root: Mock,
        mock_show_structure: Mock,
    ) -> None:
        """Test structure command with JSON format."""
        mock_get_root.return_value = Path('/test')
        mock_interactor = Mock()
        mock_show_structure.return_value = mock_interactor

        # Mock binder data
        mock_binder = Mock()
        mock_item = Mock()
        mock_item.display_title = 'Test Item'
        mock_item.id = 'test-id'
        mock_item.children = []
        mock_binder.roots = [mock_item]
        mock_binder_repo.return_value.load.return_value = mock_binder

        result = self.runner.invoke(app, ['structure', '--format', 'json'])

        assert result.exit_code == 0
        data = json.loads(result.stdout)
        assert 'roots' in data

    @patch('prosemark.cli.main.ShowStructure')
    @patch('prosemark.cli.main._get_project_root')
    @patch('prosemark.cli.main.BinderRepoFs')
    def test_structure_command_unknown_format(
        self,
        mock_binder_repo: Mock,
        mock_get_root: Mock,
        mock_show_structure: Mock,
    ) -> None:
        """Test structure command with unknown format."""
        mock_get_root.return_value = Path('/test')

        result = self.runner.invoke(app, ['structure', '--format', 'unknown'])

        assert result.exit_code == 1
        assert "Error: Unknown format 'unknown'" in result.stdout

    @patch('prosemark.cli.main.ShowStructure')
    @patch('prosemark.cli.main._get_project_root')
    @patch('prosemark.cli.main.BinderRepoFs')
    def test_structure_command_filesystem_error(
        self,
        mock_binder_repo: Mock,
        mock_get_root: Mock,
        mock_show_structure: Mock,
    ) -> None:
        """Test structure command with filesystem error."""
        mock_get_root.return_value = Path('/test')
        mock_binder_repo.side_effect = FileSystemError('Cannot read binder')

        result = self.runner.invoke(app, ['structure'])

        assert result.exit_code == 1
        assert 'Error: Cannot read binder' in result.stdout

    @patch('prosemark.cli.main.AuditBinder')
    @patch('prosemark.cli.main._get_project_root')
    @patch('prosemark.cli.main.BinderRepoFs')
    @patch('prosemark.cli.main.NodeRepoFs')
    def test_audit_command_clean_project(
        self,
        mock_node_repo: Mock,
        mock_binder_repo: Mock,
        mock_get_root: Mock,
        mock_audit: Mock,
    ) -> None:
        """Test audit command with clean project."""
        mock_get_root.return_value = Path('/test')
        mock_interactor = Mock()
        mock_audit.return_value = mock_interactor

        # Mock clean audit report
        mock_report = Mock()
        mock_report.is_clean.return_value = True
        mock_report.placeholders = []
        mock_report.missing = []
        mock_report.orphans = []
        mock_report.mismatches = []
        mock_interactor.execute.return_value = mock_report

        result = self.runner.invoke(app, ['audit'])

        assert result.exit_code == 0
        assert 'Project integrity check completed' in result.stdout

    @patch('prosemark.cli.main.AuditBinder')
    @patch('prosemark.cli.main._get_project_root')
    @patch('prosemark.cli.main.BinderRepoFs')
    @patch('prosemark.cli.main.NodeRepoFs')
    def test_audit_command_with_issues(
        self,
        mock_node_repo: Mock,
        mock_binder_repo: Mock,
        mock_get_root: Mock,
        mock_audit: Mock,
    ) -> None:
        """Test audit command with integrity issues."""
        mock_get_root.return_value = Path('/test')
        mock_interactor = Mock()
        mock_audit.return_value = mock_interactor

        # Mock audit report with placeholders only (should not cause failure)
        mock_placeholder = Mock()
        mock_placeholder.display_title = 'Missing Placeholder'

        mock_report = Mock()
        mock_report.is_clean.return_value = True  # Clean with my new logic (no real issues)
        mock_report.placeholders = [mock_placeholder]
        mock_report.missing = []
        mock_report.orphans = []
        mock_report.mismatches = []
        mock_interactor.execute.return_value = mock_report

        result = self.runner.invoke(app, ['audit'])

        assert result.exit_code == 0  # Placeholders don't cause failure
        assert 'PLACEHOLDER: "Missing Placeholder"' in result.stdout
        assert 'Project integrity check completed' in result.stdout

    @patch('prosemark.cli.main.AuditBinder')
    @patch('prosemark.cli.main._get_project_root')
    @patch('prosemark.cli.main.BinderRepoFs')
    @patch('prosemark.cli.main.NodeRepoFs')
    def test_audit_command_with_fix_flag(
        self,
        mock_node_repo: Mock,
        mock_binder_repo: Mock,
        mock_get_root: Mock,
        mock_audit: Mock,
    ) -> None:
        """Test audit command with fix flag."""
        mock_get_root.return_value = Path('/test')
        mock_interactor = Mock()
        mock_audit.return_value = mock_interactor

        # Mock audit report with real issues to trigger fix behavior
        mock_missing = Mock()
        mock_missing.node_id = 'missing123'

        mock_report = Mock()
        mock_report.is_clean.return_value = False
        mock_report.placeholders = []
        mock_report.missing = [mock_missing]
        mock_report.orphans = []
        mock_report.mismatches = []
        mock_interactor.execute.return_value = mock_report

        result = self.runner.invoke(app, ['audit', '--fix'])

        assert result.exit_code == 2
        assert 'Note: Auto-fix not implemented in MVP' in result.stdout

    @patch('prosemark.cli.main.AddNode')
    @patch('prosemark.cli.main._get_project_root')
    @patch('prosemark.cli.main.BinderRepoFs')
    @patch('prosemark.cli.main.NodeRepoFs')
    @patch('prosemark.cli.main.IdGeneratorUuid7')
    def test_add_command_node_not_found_error(
        self,
        mock_id_gen: Mock,
        mock_node_repo: Mock,
        mock_binder_repo: Mock,
        mock_get_root: Mock,
        mock_add_node: Mock,
    ) -> None:
        """Test add command with NodeNotFoundError."""
        mock_get_root.return_value = Path('/test')
        mock_interactor = Mock()
        mock_add_node.return_value = mock_interactor
        mock_interactor.execute.side_effect = NodeNotFoundError('Node not found')

        result = self.runner.invoke(app, ['add', 'Test Node'])

        assert result.exit_code == 1
        assert 'Error: Parent node not found' in result.stdout

    @patch('prosemark.cli.main.AddNode')
    @patch('prosemark.cli.main._get_project_root')
    @patch('prosemark.cli.main.BinderRepoFs')
    @patch('prosemark.cli.main.NodeRepoFs')
    @patch('prosemark.cli.main.IdGeneratorUuid7')
    def test_add_command_value_error(
        self,
        mock_id_gen: Mock,
        mock_node_repo: Mock,
        mock_binder_repo: Mock,
        mock_get_root: Mock,
        mock_add_node: Mock,
    ) -> None:
        """Test add command with ValueError."""
        mock_get_root.return_value = Path('/test')
        mock_interactor = Mock()
        mock_add_node.return_value = mock_interactor
        mock_interactor.execute.side_effect = ValueError('Invalid position')

        result = self.runner.invoke(app, ['add', 'Test Node'])

        assert result.exit_code == 2
        assert 'Error: Invalid position index' in result.stdout

    @patch('prosemark.cli.main.AddNode')
    @patch('prosemark.cli.main._get_project_root')
    @patch('prosemark.cli.main.BinderRepoFs')
    @patch('prosemark.cli.main.NodeRepoFs')
    @patch('prosemark.cli.main.IdGeneratorUuid7')
    def test_add_command_filesystem_error(
        self,
        mock_id_gen: Mock,
        mock_node_repo: Mock,
        mock_binder_repo: Mock,
        mock_get_root: Mock,
        mock_add_node: Mock,
    ) -> None:
        """Test add command with FileSystemError."""
        mock_get_root.return_value = Path('/test')
        mock_interactor = Mock()
        mock_add_node.return_value = mock_interactor
        mock_interactor.execute.side_effect = FileSystemError('Permission denied')

        result = self.runner.invoke(app, ['add', 'Test Node'])

        assert result.exit_code == 3
        assert 'Error: File creation failed - Permission denied' in result.stdout

    @patch('prosemark.cli.main.app')
    def test_main_function_calls_app(self, mock_app: Mock) -> None:
        """Test that main function calls the typer app."""
        from prosemark.cli.main import main

        main()

        mock_app.assert_called_once()


class TestEditCommand:
    """Test edit command functionality."""

    def setup_method(self) -> None:
        """Set up test environment."""
        self.runner = CliRunner()

    @patch('prosemark.cli.main.EditPart')
    @patch('prosemark.cli.main._get_project_root')
    @patch('prosemark.cli.main.BinderRepoFs')
    @patch('prosemark.cli.main.NodeRepoFs')
    @patch('prosemark.cli.main.EditorLauncherSystem')
    @patch('prosemark.cli.main.ClockSystem')
    @patch('prosemark.cli.main.LoggerStdout')
    def test_edit_command_success_draft(
        self,
        mock_logger: Mock,
        mock_clock: Mock,
        mock_editor: Mock,
        mock_node_repo: Mock,
        mock_binder_repo: Mock,
        mock_get_root: Mock,
        mock_edit_part: Mock,
    ) -> None:
        """Test successful edit command for draft part."""
        valid_node_id = str(NodeId.generate())
        mock_get_root.return_value = Path('/test')
        mock_interactor = Mock()
        mock_edit_part.return_value = mock_interactor

        result = self.runner.invoke(app, ['edit', valid_node_id])

        assert result.exit_code == 0
        assert f'Opened {valid_node_id}.md in editor' in result.stdout

    @patch('prosemark.cli.main.EditPart')
    @patch('prosemark.cli.main._get_project_root')
    @patch('prosemark.cli.main.BinderRepoFs')
    @patch('prosemark.cli.main.NodeRepoFs')
    @patch('prosemark.cli.main.EditorLauncherSystem')
    @patch('prosemark.cli.main.ClockSystem')
    @patch('prosemark.cli.main.LoggerStdout')
    def test_edit_command_success_notes(
        self,
        mock_logger: Mock,
        mock_clock: Mock,
        mock_editor: Mock,
        mock_node_repo: Mock,
        mock_binder_repo: Mock,
        mock_get_root: Mock,
        mock_edit_part: Mock,
    ) -> None:
        """Test successful edit command for notes part."""
        valid_node_id = str(NodeId.generate())
        mock_get_root.return_value = Path('/test')
        mock_interactor = Mock()
        mock_edit_part.return_value = mock_interactor

        result = self.runner.invoke(app, ['edit', valid_node_id, '--part', 'notes'])

        assert result.exit_code == 0
        assert f'Opened {valid_node_id}.notes.md in editor' in result.stdout

    @patch('prosemark.cli.main.EditPart')
    @patch('prosemark.cli.main._get_project_root')
    @patch('prosemark.cli.main.BinderRepoFs')
    @patch('prosemark.cli.main.NodeRepoFs')
    @patch('prosemark.cli.main.EditorLauncherSystem')
    @patch('prosemark.cli.main.ClockSystem')
    @patch('prosemark.cli.main.LoggerStdout')
    def test_edit_command_success_other_part(
        self,
        mock_logger: Mock,
        mock_clock: Mock,
        mock_editor: Mock,
        mock_node_repo: Mock,
        mock_binder_repo: Mock,
        mock_get_root: Mock,
        mock_edit_part: Mock,
    ) -> None:
        """Test successful edit command for other part."""
        valid_node_id = str(NodeId.generate())
        mock_get_root.return_value = Path('/test')
        mock_interactor = Mock()
        mock_edit_part.return_value = mock_interactor

        result = self.runner.invoke(app, ['edit', valid_node_id, '--part', 'summary'])

        assert result.exit_code == 0
        assert f'Opened summary for {valid_node_id} in editor' in result.stdout

    @patch('prosemark.cli.main.EditPart')
    @patch('prosemark.cli.main._get_project_root')
    @patch('prosemark.cli.main.BinderRepoFs')
    @patch('prosemark.cli.main.NodeRepoFs')
    @patch('prosemark.cli.main.EditorLauncherSystem')
    @patch('prosemark.cli.main.ClockSystem')
    @patch('prosemark.cli.main.LoggerStdout')
    def test_edit_command_node_not_found_error(
        self,
        mock_logger: Mock,
        mock_clock: Mock,
        mock_editor: Mock,
        mock_node_repo: Mock,
        mock_binder_repo: Mock,
        mock_get_root: Mock,
        mock_edit_part: Mock,
    ) -> None:
        """Test edit command with NodeNotFoundError."""
        valid_node_id = str(NodeId.generate())
        mock_get_root.return_value = Path('/test')
        mock_interactor = Mock()
        mock_edit_part.return_value = mock_interactor
        mock_interactor.execute.side_effect = NodeNotFoundError('Node not found')

        result = self.runner.invoke(app, ['edit', valid_node_id])

        assert result.exit_code == 1
        assert 'Error: Node not found' in result.stdout

    @patch('prosemark.cli.main.EditPart')
    @patch('prosemark.cli.main._get_project_root')
    @patch('prosemark.cli.main.BinderRepoFs')
    @patch('prosemark.cli.main.NodeRepoFs')
    @patch('prosemark.cli.main.EditorLauncherSystem')
    @patch('prosemark.cli.main.ClockSystem')
    @patch('prosemark.cli.main.LoggerStdout')
    def test_edit_command_editor_launch_error(
        self,
        mock_logger: Mock,
        mock_clock: Mock,
        mock_editor: Mock,
        mock_node_repo: Mock,
        mock_binder_repo: Mock,
        mock_get_root: Mock,
        mock_edit_part: Mock,
    ) -> None:
        """Test edit command with EditorLaunchError."""
        valid_node_id = str(NodeId.generate())
        mock_get_root.return_value = Path('/test')
        mock_interactor = Mock()
        mock_edit_part.return_value = mock_interactor
        mock_interactor.execute.side_effect = EditorLaunchError('No editor')

        result = self.runner.invoke(app, ['edit', valid_node_id])

        assert result.exit_code == 2
        assert 'Error: Editor not available' in result.stdout

    @patch('prosemark.cli.main.EditPart')
    @patch('prosemark.cli.main._get_project_root')
    @patch('prosemark.cli.main.BinderRepoFs')
    @patch('prosemark.cli.main.NodeRepoFs')
    @patch('prosemark.cli.main.EditorLauncherSystem')
    @patch('prosemark.cli.main.ClockSystem')
    @patch('prosemark.cli.main.LoggerStdout')
    def test_edit_command_filesystem_error(
        self,
        mock_logger: Mock,
        mock_clock: Mock,
        mock_editor: Mock,
        mock_node_repo: Mock,
        mock_binder_repo: Mock,
        mock_get_root: Mock,
        mock_edit_part: Mock,
    ) -> None:
        """Test edit command with FileSystemError."""
        valid_node_id = str(NodeId.generate())
        mock_get_root.return_value = Path('/test')
        mock_interactor = Mock()
        mock_edit_part.return_value = mock_interactor
        mock_interactor.execute.side_effect = FileSystemError('Permission denied')

        result = self.runner.invoke(app, ['edit', valid_node_id])

        assert result.exit_code == 3
        assert 'Error: File permission denied' in result.stdout

    @patch('prosemark.cli.main.EditPart')
    @patch('prosemark.cli.main._get_project_root')
    @patch('prosemark.cli.main.BinderRepoFs')
    @patch('prosemark.cli.main.NodeRepoFs')
    @patch('prosemark.cli.main.EditorLauncherSystem')
    @patch('prosemark.cli.main.ClockSystem')
    @patch('prosemark.cli.main.LoggerStdout')
    def test_edit_command_value_error(
        self,
        mock_logger: Mock,
        mock_clock: Mock,
        mock_editor: Mock,
        mock_node_repo: Mock,
        mock_binder_repo: Mock,
        mock_get_root: Mock,
        mock_edit_part: Mock,
    ) -> None:
        """Test edit command with ValueError."""
        valid_node_id = str(NodeId.generate())
        mock_get_root.return_value = Path('/test')
        mock_interactor = Mock()
        mock_edit_part.return_value = mock_interactor
        mock_interactor.execute.side_effect = ValueError('Invalid part')

        result = self.runner.invoke(app, ['edit', valid_node_id])

        assert result.exit_code == 1
        assert 'Error: Invalid part' in result.stdout


class TestMaterializeCommand:
    """Test materialize command functionality."""

    def setup_method(self) -> None:
        """Set up test environment."""
        self.runner = CliRunner()

    @patch('prosemark.cli.main.MaterializeNodeUseCase')
    @patch('prosemark.cli.main._get_project_root')
    @patch('prosemark.cli.main.BinderRepoFs')
    @patch('prosemark.cli.main.NodeRepoFs')
    @patch('prosemark.cli.main.IdGeneratorUuid7')
    @patch('prosemark.cli.main.EditorLauncherSystem')
    @patch('prosemark.cli.main.ClockSystem')
    @patch('prosemark.cli.main.LoggerStdout')
    def test_materialize_command_success(
        self,
        mock_logger: Mock,
        mock_clock: Mock,
        mock_editor: Mock,
        mock_id_gen: Mock,
        mock_node_repo: Mock,
        mock_binder_repo: Mock,
        mock_get_root: Mock,
        mock_materialize: Mock,
    ) -> None:
        """Test successful materialize command."""
        valid_node_id = NodeId.generate()
        mock_get_root.return_value = Path('/test')
        mock_interactor = Mock()
        mock_materialize.return_value = mock_interactor
        mock_interactor.execute.return_value = MaterializeResult(valid_node_id, was_already_materialized=False)

        result = self.runner.invoke(app, ['materialize', 'Test Node'])

        assert result.exit_code == 0
        assert f'Materialized "Test Node" ({valid_node_id.value})' in result.stdout
        assert f'Created files: {valid_node_id.value}.md, {valid_node_id.value}.notes.md' in result.stdout
        assert 'Updated binder structure' in result.stdout

    @patch('prosemark.cli.main.MaterializeNodeUseCase')
    @patch('prosemark.cli.main._get_project_root')
    @patch('prosemark.cli.main.BinderRepoFs')
    @patch('prosemark.cli.main.NodeRepoFs')
    @patch('prosemark.cli.main.IdGeneratorUuid7')
    @patch('prosemark.cli.main.EditorLauncherSystem')
    @patch('prosemark.cli.main.ClockSystem')
    @patch('prosemark.cli.main.LoggerStdout')
    def test_materialize_command_placeholder_not_found(
        self,
        mock_logger: Mock,
        mock_clock: Mock,
        mock_editor: Mock,
        mock_id_gen: Mock,
        mock_node_repo: Mock,
        mock_binder_repo: Mock,
        mock_get_root: Mock,
        mock_materialize: Mock,
    ) -> None:
        """Test materialize command with PlaceholderNotFoundError."""
        mock_get_root.return_value = Path('/test')
        mock_interactor = Mock()
        mock_materialize.return_value = mock_interactor
        mock_interactor.execute.side_effect = PlaceholderNotFoundError('Not found')

        result = self.runner.invoke(app, ['materialize', 'Test Node'])

        assert result.exit_code == 1
        assert 'Error: Placeholder not found' in result.stdout

    @patch('prosemark.cli.main.MaterializeNodeUseCase')
    @patch('prosemark.cli.main._get_project_root')
    @patch('prosemark.cli.main.BinderRepoFs')
    @patch('prosemark.cli.main.NodeRepoFs')
    @patch('prosemark.cli.main.IdGeneratorUuid7')
    @patch('prosemark.cli.main.EditorLauncherSystem')
    @patch('prosemark.cli.main.ClockSystem')
    @patch('prosemark.cli.main.LoggerStdout')
    def test_materialize_command_already_materialized(
        self,
        mock_logger: Mock,
        mock_clock: Mock,
        mock_editor: Mock,
        mock_id_gen: Mock,
        mock_node_repo: Mock,
        mock_binder_repo: Mock,
        mock_get_root: Mock,
        mock_materialize: Mock,
    ) -> None:
        """Test materialize command with already materialized item."""
        existing_node_id = NodeId.generate()
        mock_get_root.return_value = Path('/test')
        mock_interactor = Mock()
        mock_materialize.return_value = mock_interactor
        mock_interactor.execute.return_value = MaterializeResult(existing_node_id, was_already_materialized=True)

        result = self.runner.invoke(app, ['materialize', 'Test Node'])

        assert result.exit_code == 0
        assert result.stdout.strip() == ''  # CLI should be silent for already-materialized items

    @patch('prosemark.cli.main.MaterializeNodeUseCase')
    @patch('prosemark.cli.main._get_project_root')
    @patch('prosemark.cli.main.BinderRepoFs')
    @patch('prosemark.cli.main.NodeRepoFs')
    @patch('prosemark.cli.main.IdGeneratorUuid7')
    @patch('prosemark.cli.main.EditorLauncherSystem')
    @patch('prosemark.cli.main.ClockSystem')
    @patch('prosemark.cli.main.LoggerStdout')
    def test_materialize_command_filesystem_error(
        self,
        mock_logger: Mock,
        mock_clock: Mock,
        mock_editor: Mock,
        mock_id_gen: Mock,
        mock_node_repo: Mock,
        mock_binder_repo: Mock,
        mock_get_root: Mock,
        mock_materialize: Mock,
    ) -> None:
        """Test materialize command with FileSystemError."""
        mock_get_root.return_value = Path('/test')
        mock_interactor = Mock()
        mock_materialize.return_value = mock_interactor
        mock_interactor.execute.side_effect = FileSystemError('Permission denied')

        result = self.runner.invoke(app, ['materialize', 'Test Node'])

        assert result.exit_code == 2, f'Expected exit code 2, got {result.exit_code}. Output: {result.output}'
        assert 'Error: File creation failed' in result.stdout


class TestMoveCommand:
    """Test move command functionality."""

    def setup_method(self) -> None:
        """Set up test environment."""
        self.runner = CliRunner()

    @patch('prosemark.cli.main.MoveNode')
    @patch('prosemark.cli.main._get_project_root')
    @patch('prosemark.cli.main.BinderRepoFs')
    @patch('prosemark.cli.main.LoggerStdout')
    def test_move_command_success_to_root(
        self,
        mock_logger: Mock,
        mock_binder_repo: Mock,
        mock_get_root: Mock,
        mock_move_node: Mock,
    ) -> None:
        """Test successful move command to root."""
        valid_node_id = str(NodeId.generate())
        mock_get_root.return_value = Path('/test')
        mock_interactor = Mock()
        mock_move_node.return_value = mock_interactor

        result = self.runner.invoke(app, ['move', valid_node_id])

        assert result.exit_code == 0
        assert 'Moved node to root' in result.stdout
        assert 'Updated binder structure' in result.stdout

    @patch('prosemark.cli.main.MoveNode')
    @patch('prosemark.cli.main._get_project_root')
    @patch('prosemark.cli.main.BinderRepoFs')
    @patch('prosemark.cli.main.LoggerStdout')
    def test_move_command_success_with_parent_and_position(
        self,
        mock_logger: Mock,
        mock_binder_repo: Mock,
        mock_get_root: Mock,
        mock_move_node: Mock,
    ) -> None:
        """Test successful move command with parent and position."""
        valid_node_id = str(NodeId.generate())
        parent_id = str(NodeId.generate())
        mock_get_root.return_value = Path('/test')
        mock_interactor = Mock()
        mock_move_node.return_value = mock_interactor

        result = self.runner.invoke(app, ['move', valid_node_id, '--parent', parent_id, '--position', '2'])

        assert result.exit_code == 0
        assert f'Moved node to parent {parent_id} at position 2' in result.stdout
        assert 'Updated binder structure' in result.stdout

    @patch('prosemark.cli.main.MoveNode')
    @patch('prosemark.cli.main._get_project_root')
    @patch('prosemark.cli.main.BinderRepoFs')
    @patch('prosemark.cli.main.LoggerStdout')
    def test_move_command_node_not_found_error(
        self,
        mock_logger: Mock,
        mock_binder_repo: Mock,
        mock_get_root: Mock,
        mock_move_node: Mock,
    ) -> None:
        """Test move command with NodeNotFoundError."""
        valid_node_id = str(NodeId.generate())
        mock_get_root.return_value = Path('/test')
        mock_interactor = Mock()
        mock_move_node.return_value = mock_interactor
        mock_interactor.execute.side_effect = NodeNotFoundError('Node not found')

        result = self.runner.invoke(app, ['move', valid_node_id])

        assert result.exit_code == 1
        assert 'Error: Node not found' in result.stdout

    @patch('prosemark.cli.main.MoveNode')
    @patch('prosemark.cli.main._get_project_root')
    @patch('prosemark.cli.main.BinderRepoFs')
    @patch('prosemark.cli.main.LoggerStdout')
    def test_move_command_value_error(
        self,
        mock_logger: Mock,
        mock_binder_repo: Mock,
        mock_get_root: Mock,
        mock_move_node: Mock,
    ) -> None:
        """Test move command with ValueError."""
        valid_node_id = str(NodeId.generate())
        mock_get_root.return_value = Path('/test')
        mock_interactor = Mock()
        mock_move_node.return_value = mock_interactor
        mock_interactor.execute.side_effect = ValueError('Invalid position')

        result = self.runner.invoke(app, ['move', valid_node_id])

        assert result.exit_code == 2
        assert 'Error: Invalid parent or position' in result.stdout

    @patch('prosemark.cli.main.MoveNode')
    @patch('prosemark.cli.main._get_project_root')
    @patch('prosemark.cli.main.BinderRepoFs')
    @patch('prosemark.cli.main.LoggerStdout')
    def test_move_command_binder_integrity_error(
        self,
        mock_logger: Mock,
        mock_binder_repo: Mock,
        mock_get_root: Mock,
        mock_move_node: Mock,
    ) -> None:
        """Test move command with BinderIntegrityError."""
        valid_node_id = str(NodeId.generate())
        mock_get_root.return_value = Path('/test')
        mock_interactor = Mock()
        mock_move_node.return_value = mock_interactor
        mock_interactor.execute.side_effect = BinderIntegrityError('Circular reference')

        result = self.runner.invoke(app, ['move', valid_node_id])

        assert result.exit_code == 3
        assert 'Error: Would create circular reference' in result.stdout


class TestRemoveCommand:
    """Test remove command functionality."""

    def setup_method(self) -> None:
        """Set up test environment."""
        self.runner = CliRunner()

    @patch('prosemark.cli.main.RemoveNode')
    @patch('prosemark.cli.main._get_project_root')
    @patch('prosemark.cli.main.BinderRepoFs')
    @patch('prosemark.cli.main.NodeRepoFs')
    @patch('prosemark.cli.main.EditorLauncherSystem')
    @patch('prosemark.cli.main.ClockSystem')
    @patch('prosemark.cli.main.LoggerStdout')
    def test_remove_command_success_preserve_files(
        self,
        mock_logger: Mock,
        mock_clock: Mock,
        mock_editor: Mock,
        mock_node_repo: Mock,
        mock_binder_repo: Mock,
        mock_get_root: Mock,
        mock_remove_node: Mock,
    ) -> None:
        """Test successful remove command preserving files."""
        valid_node_id = str(NodeId.generate())
        mock_get_root.return_value = Path('/test')
        mock_interactor = Mock()
        mock_remove_node.return_value = mock_interactor

        # Mock binder to find node
        mock_binder = Mock()
        mock_item = Mock()
        mock_item.display_title = 'Test Node'
        mock_binder.find_by_id.return_value = mock_item
        mock_binder_repo.return_value.load.return_value = mock_binder

        result = self.runner.invoke(app, ['remove', valid_node_id])

        assert result.exit_code == 0
        assert 'Removed "Test Node" from binder' in result.stdout
        assert f'Files preserved: {valid_node_id}.md, {valid_node_id}.notes.md' in result.stdout

    @patch('prosemark.cli.main.RemoveNode')
    @patch('prosemark.cli.main._get_project_root')
    @patch('prosemark.cli.main.BinderRepoFs')
    @patch('prosemark.cli.main.NodeRepoFs')
    @patch('prosemark.cli.main.EditorLauncherSystem')
    @patch('prosemark.cli.main.ClockSystem')
    @patch('prosemark.cli.main.LoggerStdout')
    def test_remove_command_success_delete_files_forced(
        self,
        mock_logger: Mock,
        mock_clock: Mock,
        mock_editor: Mock,
        mock_node_repo: Mock,
        mock_binder_repo: Mock,
        mock_get_root: Mock,
        mock_remove_node: Mock,
    ) -> None:
        """Test successful remove command deleting files with force."""
        valid_node_id = str(NodeId.generate())
        mock_get_root.return_value = Path('/test')
        mock_interactor = Mock()
        mock_remove_node.return_value = mock_interactor

        # Mock binder to find node
        mock_binder = Mock()
        mock_item = Mock()
        mock_item.display_title = 'Test Node'
        mock_binder.find_by_id.return_value = mock_item
        mock_binder_repo.return_value.load.return_value = mock_binder

        result = self.runner.invoke(app, ['remove', valid_node_id, '--delete-files', '--force'])

        assert result.exit_code == 0
        assert 'Removed "Test Node" from binder' in result.stdout
        assert f'Deleted files: {valid_node_id}.md, {valid_node_id}.notes.md' in result.stdout

    @patch('prosemark.cli.main.RemoveNode')
    @patch('prosemark.cli.main._get_project_root')
    @patch('prosemark.cli.main.BinderRepoFs')
    @patch('prosemark.cli.main.NodeRepoFs')
    @patch('prosemark.cli.main.EditorLauncherSystem')
    @patch('prosemark.cli.main.ClockSystem')
    @patch('prosemark.cli.main.LoggerStdout')
    @patch('typer.confirm')
    def test_remove_command_confirmation_cancelled(
        self,
        mock_confirm: Mock,
        mock_logger: Mock,
        mock_clock: Mock,
        mock_editor: Mock,
        mock_node_repo: Mock,
        mock_binder_repo: Mock,
        mock_get_root: Mock,
        mock_remove_node: Mock,
    ) -> None:
        """Test remove command with cancelled confirmation."""
        valid_node_id = str(NodeId.generate())
        mock_get_root.return_value = Path('/test')
        mock_confirm.return_value = False

        result = self.runner.invoke(app, ['remove', valid_node_id, '--delete-files'])

        assert result.exit_code == 2
        assert 'Operation cancelled' in result.stdout

    @patch('prosemark.cli.main.RemoveNode')
    @patch('prosemark.cli.main._get_project_root')
    @patch('prosemark.cli.main.BinderRepoFs')
    @patch('prosemark.cli.main.NodeRepoFs')
    @patch('prosemark.cli.main.EditorLauncherSystem')
    @patch('prosemark.cli.main.ClockSystem')
    @patch('prosemark.cli.main.LoggerStdout')
    def test_remove_command_node_not_found_error(
        self,
        mock_logger: Mock,
        mock_clock: Mock,
        mock_editor: Mock,
        mock_node_repo: Mock,
        mock_binder_repo: Mock,
        mock_get_root: Mock,
        mock_remove_node: Mock,
    ) -> None:
        """Test remove command with NodeNotFoundError."""
        valid_node_id = str(NodeId.generate())
        mock_get_root.return_value = Path('/test')
        mock_interactor = Mock()
        mock_remove_node.return_value = mock_interactor
        mock_interactor.execute.side_effect = NodeNotFoundError('Node not found')

        # Mock binder to not find node
        mock_binder = Mock()
        mock_binder.find_by_id.return_value = None
        mock_binder_repo.return_value.load.return_value = mock_binder

        result = self.runner.invoke(app, ['remove', valid_node_id])

        assert result.exit_code == 1
        assert 'Error: Node not found' in result.stdout

    @patch('prosemark.cli.main.RemoveNode')
    @patch('prosemark.cli.main._get_project_root')
    @patch('prosemark.cli.main.BinderRepoFs')
    @patch('prosemark.cli.main.NodeRepoFs')
    @patch('prosemark.cli.main.EditorLauncherSystem')
    @patch('prosemark.cli.main.ClockSystem')
    @patch('prosemark.cli.main.LoggerStdout')
    def test_remove_command_filesystem_error(
        self,
        mock_logger: Mock,
        mock_clock: Mock,
        mock_editor: Mock,
        mock_node_repo: Mock,
        mock_binder_repo: Mock,
        mock_get_root: Mock,
        mock_remove_node: Mock,
    ) -> None:
        """Test remove command with FileSystemError."""
        valid_node_id = str(NodeId.generate())
        mock_get_root.return_value = Path('/test')
        mock_interactor = Mock()
        mock_remove_node.return_value = mock_interactor
        mock_interactor.execute.side_effect = FileSystemError('Permission denied')

        # Mock binder to find node
        mock_binder = Mock()
        mock_item = Mock()
        mock_item.display_title = 'Test Node'
        mock_binder.find_by_id.return_value = mock_item
        mock_binder_repo.return_value.load.return_value = mock_binder

        result = self.runner.invoke(app, ['remove', valid_node_id])

        assert result.exit_code == 3
        assert 'Error: File deletion failed' in result.stdout


class TestAuditCommandExtended:
    """Extended test audit command functionality."""

    def setup_method(self) -> None:
        """Set up test environment."""
        self.runner = CliRunner()

    @patch('prosemark.cli.main.AuditBinder')
    @patch('prosemark.cli.main._get_project_root')
    @patch('prosemark.cli.main.BinderRepoFs')
    @patch('prosemark.cli.main.NodeRepoFs')
    def test_audit_command_with_all_issue_types(
        self,
        mock_node_repo: Mock,
        mock_binder_repo: Mock,
        mock_get_root: Mock,
        mock_audit: Mock,
    ) -> None:
        """Test audit command with all types of issues."""
        mock_get_root.return_value = Path('/test')
        mock_interactor = Mock()
        mock_audit.return_value = mock_interactor

        # Mock audit report with all issue types
        mock_placeholder = Mock()
        mock_placeholder.display_title = 'Missing Placeholder'

        mock_missing = Mock()
        mock_missing.node_id = 'missing-node-id'

        mock_orphan = Mock()
        mock_orphan.file_path = '/test/orphan.md'

        mock_mismatch = Mock()
        mock_mismatch.file_path = '/test/mismatch.md'

        mock_report = Mock()
        mock_report.is_clean.return_value = False
        mock_report.placeholders = [mock_placeholder]
        mock_report.missing = [mock_missing]
        mock_report.orphans = [mock_orphan]
        mock_report.mismatches = [mock_mismatch]
        mock_interactor.execute.return_value = mock_report

        result = self.runner.invoke(app, ['audit'])

        assert result.exit_code == 1
        # Placeholders are shown first (informational)
        assert '⚠ PLACEHOLDER: "Missing Placeholder"' in result.stdout
        # Then real issues
        assert 'Project integrity issues found:' in result.stdout
        assert '⚠ MISSING: Node missing-node-id referenced but files not found' in result.stdout
        assert '⚠ ORPHAN: File /test/orphan.md exists but not in binder' in result.stdout
        assert '⚠ MISMATCH: File /test/mismatch.md ID mismatch' in result.stdout


class TestMainAppCLIBasics:
    """Test basic CLI functionality without complex mocking."""

    def setup_method(self) -> None:
        """Set up test environment."""
        self.runner = CliRunner()

    def test_main_app_help(self) -> None:
        """Test that the main app help works."""
        result = self.runner.invoke(app, ['--help'])

        assert result.exit_code == 0
        assert 'Prosemark CLI' in result.stdout

    def test_invalid_command(self) -> None:
        """Test invalid command handling."""
        result = self.runner.invoke(app, ['invalid-command'])

        assert result.exit_code != 0
