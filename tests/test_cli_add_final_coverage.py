"""Final coverage tests for remaining cli/add.py gaps."""

from pathlib import Path
from unittest.mock import MagicMock, patch

from click.testing import CliRunner

from prosemark.cli.add import add_command
from prosemark.templates.domain.exceptions.template_exceptions import TemplateNotFoundError


class TestCLIAddFinalCoverage:
    """Cover remaining uncovered lines in cli/add.py."""

    def test_list_templates_error_from_use_case(self) -> None:
        """Test line 133: handle error from list_templates use case."""
        runner = CliRunner(mix_stderr=False)

        with runner.isolated_filesystem():
            templates_dir = Path('templates')
            templates_dir.mkdir()

            # Mock the container and use case to return error
            with patch('prosemark.cli.add.TemplatesContainer') as mock_container_class:
                mock_container = MagicMock()
                mock_container_class.return_value = mock_container

                mock_use_case = MagicMock()
                mock_container.list_templates_use_case = mock_use_case
                # Return failure from use case
                mock_use_case.list_all_templates.return_value = {
                    'success': False,
                    'error': 'Use case error occurred',
                }

                result = runner.invoke(add_command, ['dummy-title', '--list-templates'])

                assert result.exit_code == 1
                assert 'Error listing templates' in (result.stderr or '')

    def test_template_not_found_error_handler(self) -> None:
        """Test lines 181, 385-386: handle TemplateNotFoundError with error handler."""
        runner = CliRunner(mix_stderr=False)

        with runner.isolated_filesystem():
            # Initialize project
            from prosemark.cli import init_command

            init_result = runner.invoke(init_command, ['--title', 'Test Project'])
            assert init_result.exit_code == 0

            templates_dir = Path('templates')
            templates_dir.mkdir()

            # Mock the template system to raise TemplateNotFoundError
            with patch('prosemark.cli.add.TemplatesContainer') as mock_container_class:
                mock_container = MagicMock()
                mock_container_class.return_value = mock_container

                mock_use_case = MagicMock()
                mock_container.create_from_template_use_case = mock_use_case
                # Raise TemplateNotFoundError which is caught as TemplateError
                mock_use_case.create_single_template.side_effect = TemplateNotFoundError('missing-template')

                result = runner.invoke(add_command, ['New Node', '--template', 'missing-template'])

                assert result.exit_code == 1
                # Should trigger _handle_template_not_found_error
                assert 'Template "missing-template" not found' in (result.stderr or '')

    def test_directory_template_empty_content_map(self) -> None:
        """Test line 233: handle empty content_map in directory template."""
        runner = CliRunner()

        with runner.isolated_filesystem():
            # Initialize project
            from prosemark.cli import init_command

            init_result = runner.invoke(init_command, ['--title', 'Test Project'])
            assert init_result.exit_code == 0

            templates_dir = Path('templates')
            templates_dir.mkdir()

            # Mock template system to return empty content_map
            with patch('prosemark.cli.add.TemplatesContainer') as mock_container_class:
                mock_container = MagicMock()
                mock_container_class.return_value = mock_container

                mock_use_case = MagicMock()
                mock_container.create_from_template_use_case = mock_use_case
                # Single template fails
                mock_use_case.create_single_template.return_value = {'success': False}
                # Directory template succeeds but with empty content_map
                mock_use_case.create_directory_template.return_value = {
                    'success': True,
                    'content': {},  # Empty content map
                    'file_count': 0,
                }

                result = runner.invoke(add_command, ['New Node', '--template', 'empty-dir'])

                # Should succeed but not create any node since content_map is empty
                assert result.exit_code == 0
                # The if content_map: check should prevent node creation
                assert 'Created "New Node"' in result.output
