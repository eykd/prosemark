from __future__ import annotations

from unittest.mock import patch

import pytest
from click.testing import CliRunner

from prosemark import cli
from prosemark.adapters.markdown import MarkdownFileAdapter


@pytest.fixture
def runner() -> CliRunner:
    """Create a CLI test runner."""
    return CliRunner()


def test_it_should_run_main_successfully() -> None:
    """Test that the main function runs without errors."""
    with patch('prosemark.cli.cli') as mock_cli:
        cli.main()
        mock_cli.assert_called_once_with(obj={})


def test_cli_version(runner: CliRunner) -> None:
    """Test that the CLI displays version information."""
    result = runner.invoke(cli.cli, ['--version'])
    assert result.exit_code == 0
    assert 'version' in result.output.lower()


def test_cli_help(runner: CliRunner) -> None:
    """Test that the CLI displays help information."""
    result = runner.invoke(cli.cli, ['--help'])
    assert result.exit_code == 0
    assert 'Usage:' in result.output
    assert 'Options:' in result.output
    assert 'Commands:' in result.output


def test_init_command(runner: CliRunner) -> None:
    """Test the init command creates a new project."""
    with runner.isolated_filesystem():
        with patch.object(MarkdownFileAdapter, 'create_project') as mock_create:
            mock_create.return_value = cli.Project(name='test-project')

            result = runner.invoke(cli.cli, ['--data-dir', '.', 'init', 'test-project'])

            assert result.exit_code == 0
            assert 'created successfully' in result.output
            mock_create.assert_called_once_with('test-project', '')


def test_init_command_with_description(runner: CliRunner) -> None:
    """Test the init command with a description."""
    with runner.isolated_filesystem():
        with patch.object(MarkdownFileAdapter, 'create_project') as mock_create:
            mock_create.return_value = cli.Project(name='test-project', description='Test description')

            result = runner.invoke(
                cli.cli,
                ['--data-dir', '.', 'init', 'test-project', '--description', 'Test description']
            )

            assert result.exit_code == 0
            assert 'created successfully' in result.output
            mock_create.assert_called_once_with('test-project', 'Test description')


def test_init_command_error(runner: CliRunner) -> None:
    """Test the init command handles errors."""
    with runner.isolated_filesystem():
        with patch.object(MarkdownFileAdapter, 'create_project') as mock_create:
            mock_create.side_effect = ValueError('Project already exists')

            result = runner.invoke(cli.cli, ['--data-dir', '.', 'init', 'test-project'])

            assert result.exit_code == 1
            assert 'Error:' in result.output
            assert 'Project already exists' in result.output


def test_list_command_with_projects(runner: CliRunner) -> None:
    """Test the list command shows available projects."""
    with runner.isolated_filesystem():
        with patch.object(MarkdownFileAdapter, 'list_projects') as mock_list:
            mock_list.return_value = [
                {'id': 'project1', 'name': 'Project 1'},
                {'id': 'project2', 'name': 'Project 2'},
            ]

            result = runner.invoke(cli.cli, ['--data-dir', '.', 'list'])

            assert result.exit_code == 0
            assert 'Available projects:' in result.output
            assert 'Project 1' in result.output
            assert 'Project 2' in result.output


def test_list_command_no_projects(runner: CliRunner) -> None:
    """Test the list command when no projects exist."""
    with runner.isolated_filesystem():
        with patch.object(MarkdownFileAdapter, 'list_projects') as mock_list:
            mock_list.return_value = []

            result = runner.invoke(cli.cli, ['--data-dir', '.', 'list'])

            assert result.exit_code == 0
            assert 'No projects found' in result.output
