"""Coverage tests for CLI add command uncovered lines."""

from pathlib import Path
from unittest.mock import MagicMock, patch

from click.testing import CliRunner

from prosemark.cli.add import add_command
from prosemark.exceptions import FileSystemError, NodeNotFoundError
from prosemark.templates.domain.exceptions.template_exceptions import (
    TemplateNotFoundError,
    TemplateValidationError,
    UserCancelledError,
)


class TestCLIAddCoverage:
    """Test uncovered lines in CLI add command."""

    def test_add_command_invalid_parent_id_format(self) -> None:
        """Test add command with invalid parent ID format (lines 77-78)."""
        runner = CliRunner()

        with runner.isolated_filesystem():
            from prosemark.cli import init_command

            # Initialize project first
            init_result = runner.invoke(init_command, ['--title', 'Test Project'])
            assert init_result.exit_code == 0

            # Mock NodeId constructor to raise ValueError to trigger lines 77-78
            with patch('prosemark.cli.add.NodeId') as mock_node_id:
                mock_node_id.side_effect = ValueError('Invalid UUID format')

                result = runner.invoke(add_command, ['New Chapter', '--parent', 'some-parent'])

                # Should exit with code 1 and show parent not found error
                assert result.exit_code == 1
                assert 'Error: Parent node not found' in result.output

    def test_add_command_node_not_found_error(self) -> None:
        """Test add command handles NodeNotFoundError (lines 92-93)."""
        runner = CliRunner()

        with runner.isolated_filesystem():
            from prosemark.cli import init_command

            # Initialize project first
            init_result = runner.invoke(init_command, ['--title', 'Test Project'])
            assert init_result.exit_code == 0

            # Mock the AddNode use case to raise NodeNotFoundError
            with patch('prosemark.cli.add.AddNode') as mock_add_class:
                mock_add_instance = mock_add_class.return_value
                mock_add_instance.execute.side_effect = NodeNotFoundError('Parent node not found')

                result = runner.invoke(add_command, ['New Chapter'])

                assert result.exit_code == 1
                assert 'Error: Parent node not found' in result.output

    def test_add_command_value_error(self) -> None:
        """Test add command handles ValueError (lines 95-96)."""
        runner = CliRunner()

        with runner.isolated_filesystem():
            from prosemark.cli import init_command

            # Initialize project first
            init_result = runner.invoke(init_command, ['--title', 'Test Project'])
            assert init_result.exit_code == 0

            # Mock the AddNode use case to raise ValueError
            with patch('prosemark.cli.add.AddNode') as mock_add_class:
                mock_add_instance = mock_add_class.return_value
                mock_add_instance.execute.side_effect = ValueError('Invalid position index')

                result = runner.invoke(add_command, ['New Chapter'])

                assert result.exit_code == 2
                assert 'Error: Invalid position index' in result.output

    def test_add_command_file_system_error(self) -> None:
        """Test add command handles FileSystemError (lines 98-99)."""
        runner = CliRunner()

        with runner.isolated_filesystem():
            from prosemark.cli import init_command

            # Initialize project first
            init_result = runner.invoke(init_command, ['--title', 'Test Project'])
            assert init_result.exit_code == 0

            # Mock the AddNode use case to raise FileSystemError
            with patch('prosemark.cli.add.AddNode') as mock_add_class:
                mock_add_instance = mock_add_class.return_value
                mock_add_instance.execute.side_effect = FileSystemError('Permission denied')

                result = runner.invoke(add_command, ['New Chapter'])

                assert result.exit_code == 3
                assert 'Error: File creation failed - Permission denied' in result.output

    def test_add_command_invalid_position_negative(self) -> None:
        """Test add command with negative position index (lines 68-69)."""
        runner = CliRunner()

        with runner.isolated_filesystem():
            from prosemark.cli import init_command

            # Initialize project first
            init_result = runner.invoke(init_command, ['--title', 'Test Project'])
            assert init_result.exit_code == 0

            # Try to add with negative position
            result = runner.invoke(add_command, ['New Chapter', '--position', '-1'])

            # Should exit with code 2 and show invalid position error
            assert result.exit_code == 2
            assert 'Error: Invalid position index' in result.output

    def test_add_command_auto_init_without_binder(self) -> None:
        """Test add command auto-initializes project when no binder exists (lines 32-47)."""
        runner = CliRunner()

        with (
            runner.isolated_filesystem(),
            patch('prosemark.cli.add.InitProject') as mock_init_class,
            patch('prosemark.cli.add.AddNode') as mock_add_class,
        ):
            # Don't initialize - let add command auto-initialize

            # Mock the InitProject use case to verify auto-init is called
            mock_init_instance = mock_init_class.return_value

            # Mock the AddNode use case to return a node ID
            mock_add_instance = mock_add_class.return_value
            test_node_id = 'test-node-id-123'
            mock_add_instance.execute.return_value = test_node_id

            result = runner.invoke(add_command, ['New Chapter'])

            # Should succeed and auto-initialize
            assert result.exit_code == 0

            # Verify InitProject was called (auto-init happened)
            mock_init_class.assert_called_once()
            mock_init_instance.execute.assert_called_once()

    def test_add_command_success_output(self) -> None:
        """Test add command success output (lines 87-89)."""
        runner = CliRunner()

        with runner.isolated_filesystem():
            from prosemark.cli import init_command

            # Initialize project first
            init_result = runner.invoke(init_command, ['--title', 'Test Project'])
            assert init_result.exit_code == 0

            # Mock the AddNode use case to return a known node ID
            with patch('prosemark.cli.add.AddNode') as mock_add_class:
                mock_add_instance = mock_add_class.return_value
                test_node_id = 'test-node-id-123'
                mock_add_instance.execute.return_value = test_node_id

                result = runner.invoke(add_command, ['New Chapter'])

                # Should succeed and show success output
                assert result.exit_code == 0
                assert 'Added "New Chapter" (test-node-id-123)' in result.output
                assert 'Created files: test-node-id-123.md, test-node-id-123.notes.md' in result.output
                assert 'Updated binder structure' in result.output


class TestCLIAddTemplateListingCoverage:
    """Test template listing functionality (lines 54-55, 99-136)."""

    def test_list_templates_flag_triggers_handler(self) -> None:
        """Test --list-templates flag triggers _handle_list_templates (lines 54-55)."""
        runner = CliRunner()

        with runner.isolated_filesystem():
            # Create templates directory
            Path('templates').mkdir()

            # Note: title argument is required by Click but ignored when --list-templates is used
            result = runner.invoke(add_command, ['dummy-title', '--list-templates'])

            # Should not error and should return early (not create node)
            assert result.exit_code == 0
            assert 'No templates found' in result.output

    def test_list_templates_no_directory(self) -> None:
        """Test listing templates when templates directory doesn't exist (lines 102-104)."""
        runner = CliRunner()

        with runner.isolated_filesystem():
            # Don't create templates directory
            result = runner.invoke(add_command, ['dummy-title', '--list-templates'])

            assert result.exit_code == 0
            assert 'No templates directory found' in result.output
            assert "Create './templates' directory" in result.output

    def test_list_templates_empty_directory(self) -> None:
        """Test listing templates when directory is empty (lines 113-115)."""
        runner = CliRunner()

        with runner.isolated_filesystem():
            # Create empty templates directory
            Path('templates').mkdir()

            result = runner.invoke(add_command, ['dummy-title', '--list-templates'])

            assert result.exit_code == 0
            assert 'No templates found in ./templates directory' in result.output

    def test_list_templates_with_single_templates(self) -> None:
        """Test listing single templates (lines 120-124)."""
        runner = CliRunner()

        with runner.isolated_filesystem():
            # Create templates directory with single template
            templates_dir = Path('templates')
            templates_dir.mkdir()
            (templates_dir / 'example.md').write_text('---\ntitle: "{{title}}"\n---\nContent', encoding='utf-8')

            result = runner.invoke(add_command, ['dummy-title', '--list-templates'])

            assert result.exit_code == 0
            assert 'Found 1 template(s):' in result.output
            assert 'Single templates:' in result.output
            assert '- example' in result.output

    def test_list_templates_with_directory_templates(self) -> None:
        """Test listing directory templates (lines 127-131)."""
        runner = CliRunner()

        with runner.isolated_filesystem():
            # Create templates directory with directory template
            templates_dir = Path('templates')
            templates_dir.mkdir()
            chapter_dir = templates_dir / 'chapter'
            chapter_dir.mkdir()
            (chapter_dir / 'main.md').write_text('---\ntitle: "{{title}}"\n---\nChapter', encoding='utf-8')

            result = runner.invoke(add_command, ['dummy-title', '--list-templates'])

            assert result.exit_code == 0
            assert 'Found 1 template(s):' in result.output
            assert 'Directory templates:' in result.output
            assert '- chapter' in result.output

    def test_list_templates_error_handling(self) -> None:
        """Test list templates error handling (lines 133-136)."""
        runner = CliRunner(mix_stderr=False)

        with runner.isolated_filesystem():
            templates_dir = Path('templates')
            templates_dir.mkdir()

            # Mock the container to raise an error (using TemplateNotFoundError which is caught in except clause)
            with patch('prosemark.cli.add.TemplatesContainer') as mock_container_class:
                mock_container_class.side_effect = TemplateNotFoundError('test-template')

                result = runner.invoke(add_command, ['dummy-title', '--list-templates'])

                assert result.exit_code == 1
                # Error messages go to stderr
                assert 'Error accessing templates' in (result.stderr or '')


class TestCLIAddTemplateCreationCoverage:
    """Test template creation functionality (lines 59-60, 143-187)."""

    def test_template_flag_triggers_handler(self) -> None:
        """Test --template flag triggers _handle_template_creation (lines 59-60)."""
        runner = CliRunner()

        with runner.isolated_filesystem():
            # Initialize project
            from prosemark.cli import init_command

            init_result = runner.invoke(init_command, ['--title', 'Test Project'])
            assert init_result.exit_code == 0

            # Create templates directory with a template
            templates_dir = Path('templates')
            templates_dir.mkdir()
            (templates_dir / 'example.md').write_text(
                '---\ntitle: "{{title}}"\n---\nTemplate content', encoding='utf-8'
            )

            # Mock user input to avoid interactive prompts
            with patch('prosemark.cli.add.TemplatesContainer') as mock_container_class:
                mock_container = MagicMock()
                mock_container_class.return_value = mock_container

                # Mock successful template creation
                mock_use_case = MagicMock()
                mock_container.create_from_template_use_case = mock_use_case
                mock_use_case.create_single_template.return_value = {
                    'success': True,
                    'content': 'Processed template content',
                }

                # Mock node creation
                with patch('prosemark.cli.add._create_node_with_content') as mock_create:
                    result = runner.invoke(add_command, ['New Node', '--template', 'example'])

                    assert result.exit_code == 0
                    assert 'Created "New Node" from template "example"' in result.output
                    mock_create.assert_called_once()

    def test_template_creation_no_templates_directory(self) -> None:
        """Test template creation when templates directory doesn't exist (lines 144-146)."""
        runner = CliRunner()

        with runner.isolated_filesystem():
            # Initialize project
            from prosemark.cli import init_command

            init_result = runner.invoke(init_command, ['--title', 'Test Project'])
            assert init_result.exit_code == 0

            # Don't create templates directory
            result = runner.invoke(add_command, ['New Node', '--template', 'example'])

            assert result.exit_code == 1
            assert 'No templates directory found' in result.output

    def test_template_creation_single_template_success(self) -> None:
        """Test successful single template creation (lines 154-162)."""
        runner = CliRunner()

        with runner.isolated_filesystem():
            # Initialize project
            from prosemark.cli import init_command

            init_result = runner.invoke(init_command, ['--title', 'Test Project'])
            assert init_result.exit_code == 0

            templates_dir = Path('templates')
            templates_dir.mkdir()

            # Mock the template system
            with (
                patch('prosemark.cli.add.TemplatesContainer') as mock_container_class,
                patch('prosemark.cli.add._create_node_with_content') as mock_create,
            ):
                mock_container = MagicMock()
                mock_container_class.return_value = mock_container

                mock_use_case = MagicMock()
                mock_container.create_from_template_use_case = mock_use_case
                mock_use_case.create_single_template.return_value = {
                    'success': True,
                    'content': 'Template content here',
                }

                result = runner.invoke(add_command, ['New Node', '--template', 'example'])

                assert result.exit_code == 0
                assert 'Created "New Node" from template "example"' in result.output
                mock_create.assert_called_once_with('New Node', 'Template content here', None, None, Path.cwd())

    def test_template_creation_directory_template_success(self) -> None:
        """Test successful directory template creation (lines 165-174)."""
        runner = CliRunner()

        with runner.isolated_filesystem():
            # Initialize project
            from prosemark.cli import init_command

            init_result = runner.invoke(init_command, ['--title', 'Test Project'])
            assert init_result.exit_code == 0

            templates_dir = Path('templates')
            templates_dir.mkdir()

            # Mock the template system
            with (
                patch('prosemark.cli.add.TemplatesContainer') as mock_container_class,
                patch('prosemark.cli.add._create_nodes_from_directory_template') as mock_create,
            ):
                mock_container = MagicMock()
                mock_container_class.return_value = mock_container

                mock_use_case = MagicMock()
                mock_container.create_from_template_use_case = mock_use_case
                # First call fails (not single template)
                mock_use_case.create_single_template.return_value = {'success': False}
                # Second call succeeds (directory template)
                mock_use_case.create_directory_template.return_value = {
                    'success': True,
                    'content': {'file1.md': 'Content 1', 'file2.md': 'Content 2'},
                    'file_count': 2,
                }

                result = runner.invoke(add_command, ['New Node', '--template', 'chapter'])

                assert result.exit_code == 0
                assert 'Created "New Node" with 2 files from directory template "chapter"' in result.output
                mock_create.assert_called_once()

    def test_template_creation_template_not_found(self) -> None:
        """Test template creation when template not found (lines 176-178, 180-181)."""
        runner = CliRunner()

        with runner.isolated_filesystem():
            # Initialize project
            from prosemark.cli import init_command

            init_result = runner.invoke(init_command, ['--title', 'Test Project'])
            assert init_result.exit_code == 0

            templates_dir = Path('templates')
            templates_dir.mkdir()

            # Mock the template system to fail both single and directory template
            with patch('prosemark.cli.add.TemplatesContainer') as mock_container_class:
                mock_container = MagicMock()
                mock_container_class.return_value = mock_container

                mock_use_case = MagicMock()
                mock_container.create_from_template_use_case = mock_use_case
                # Both fail
                mock_use_case.create_single_template.return_value = {'success': False, 'error': 'Not found'}
                mock_use_case.create_directory_template.return_value = {
                    'success': False,
                    'error_type': 'TemplateNotFoundError',
                    'error': 'Template not found',
                }

                result = runner.invoke(add_command, ['New Node', '--template', 'missing'])

                assert result.exit_code == 1
                # Message format: "Template error (TemplateNotFoundError): Template not found"
                assert 'Template error' in result.output or 'Template not found' in result.output

    def test_template_creation_validation_error(self) -> None:
        """Test template creation with validation error (lines 182-183)."""
        runner = CliRunner()

        with runner.isolated_filesystem():
            # Initialize project
            from prosemark.cli import init_command

            init_result = runner.invoke(init_command, ['--title', 'Test Project'])
            assert init_result.exit_code == 0

            templates_dir = Path('templates')
            templates_dir.mkdir()

            # Mock the template system to raise validation error
            with patch('prosemark.cli.add.TemplatesContainer') as mock_container_class:
                mock_container = MagicMock()
                mock_container_class.return_value = mock_container

                mock_use_case = MagicMock()
                mock_container.create_from_template_use_case = mock_use_case
                mock_use_case.create_single_template.side_effect = TemplateValidationError('Invalid template format')

                result = runner.invoke(add_command, ['New Node', '--template', 'invalid'])

                assert result.exit_code == 1
                # Message format: "Template validation error: Invalid template format"
                assert 'Template validation error' in result.output

    def test_template_creation_user_cancelled(self) -> None:
        """Test template creation when user cancels (lines 184-185)."""
        runner = CliRunner()

        with runner.isolated_filesystem():
            # Initialize project
            from prosemark.cli import init_command

            init_result = runner.invoke(init_command, ['--title', 'Test Project'])
            assert init_result.exit_code == 0

            templates_dir = Path('templates')
            templates_dir.mkdir()

            # Mock the template system to raise user cancelled error
            with patch('prosemark.cli.add.TemplatesContainer') as mock_container_class:
                mock_container = MagicMock()
                mock_container_class.return_value = mock_container

                mock_use_case = MagicMock()
                mock_container.create_from_template_use_case = mock_use_case
                mock_use_case.create_single_template.side_effect = UserCancelledError('User cancelled input')

                result = runner.invoke(add_command, ['New Node', '--template', 'example'])

                assert result.exit_code == 1
                # Message format: "Template creation cancelled by user"
                assert 'cancelled' in result.output.lower()

    def test_template_creation_file_system_error(self) -> None:
        """Test template creation with file system error (lines 186-187)."""
        runner = CliRunner()

        with runner.isolated_filesystem():
            # Initialize project
            from prosemark.cli import init_command

            init_result = runner.invoke(init_command, ['--title', 'Test Project'])
            assert init_result.exit_code == 0

            templates_dir = Path('templates')
            templates_dir.mkdir()

            # Mock the template system to raise file system error
            with patch('prosemark.cli.add.TemplatesContainer') as mock_container_class:
                mock_container = MagicMock()
                mock_container_class.return_value = mock_container

                mock_use_case = MagicMock()
                mock_container.create_from_template_use_case = mock_use_case
                mock_use_case.create_single_template.side_effect = FileSystemError('Disk full')

                result = runner.invoke(add_command, ['New Node', '--template', 'example'])

                assert result.exit_code == 1
                # Message format: "Template processing error: Disk full"
                assert 'Template processing error' in result.output


class TestCLIAddNodeCreationWithContentCoverage:
    """Test node creation with template content (lines 195-223)."""

    def test_create_node_with_content_auto_init(self) -> None:
        """Test _create_node_with_content auto-initializes project (lines 195-196)."""
        runner = CliRunner()

        with runner.isolated_filesystem():
            templates_dir = Path('templates')
            templates_dir.mkdir()
            # Create a simple template without placeholders to avoid interactive prompts
            (templates_dir / 'example.md').write_text('---\ntitle: "Example"\n---\nTest content', encoding='utf-8')

            # Don't initialize - let add command auto-initialize through template creation
            result = runner.invoke(add_command, ['New Node', '--template', 'example'])

            # Should succeed and auto-initialize
            assert result.exit_code == 0
            # The auto-initialization should have happened (visible in captured output)
            assert 'Initialized prosemark project' in result.output or 'Created "New Node"' in result.output

    def test_create_node_with_content_negative_position(self) -> None:
        """Test _create_node_with_content with negative position (lines 201-202)."""
        runner = CliRunner()

        with runner.isolated_filesystem():
            # Initialize project
            from prosemark.cli import init_command

            init_result = runner.invoke(init_command, ['--title', 'Test Project'])
            assert init_result.exit_code == 0

            templates_dir = Path('templates')
            templates_dir.mkdir()

            # Mock template system to return content
            with patch('prosemark.cli.add.TemplatesContainer') as mock_container_class:
                mock_container = MagicMock()
                mock_container_class.return_value = mock_container

                mock_use_case = MagicMock()
                mock_container.create_from_template_use_case = mock_use_case
                mock_use_case.create_single_template.return_value = {'success': True, 'content': 'Content'}

                result = runner.invoke(add_command, ['New Node', '--template', 'example', '--position', '-1'])

                # Should fail with invalid position error
                assert result.exit_code == 2
                assert 'Error: Invalid position index' in result.output

    def test_create_node_with_content_invalid_parent(self) -> None:
        """Test _create_node_with_content with invalid parent (lines 204-209)."""
        runner = CliRunner()

        with runner.isolated_filesystem():
            # Initialize project
            from prosemark.cli import init_command

            init_result = runner.invoke(init_command, ['--title', 'Test Project'])
            assert init_result.exit_code == 0

            templates_dir = Path('templates')
            templates_dir.mkdir()

            # Mock template system
            with (
                patch('prosemark.cli.add.TemplatesContainer') as mock_container_class,
                patch('prosemark.cli.add.NodeId') as mock_node_id,
            ):
                mock_container = MagicMock()
                mock_container_class.return_value = mock_container

                mock_use_case = MagicMock()
                mock_container.create_from_template_use_case = mock_use_case
                mock_use_case.create_single_template.return_value = {'success': True, 'content': 'Content'}

                # Make NodeId raise ValueError for invalid parent
                mock_node_id.side_effect = ValueError('Invalid UUID')

                result = runner.invoke(add_command, ['New Node', '--template', 'example', '--parent', 'invalid'])

                assert result.exit_code == 1
                assert 'Error: Parent node not found' in result.output

    def test_create_node_with_content_success_output(self) -> None:
        """Test _create_node_with_content success output (lines 220-223)."""
        runner = CliRunner()

        with runner.isolated_filesystem():
            # Initialize project
            from prosemark.cli import init_command

            init_result = runner.invoke(init_command, ['--title', 'Test Project'])
            assert init_result.exit_code == 0

            templates_dir = Path('templates')
            templates_dir.mkdir()

            # Mock template system
            with (
                patch('prosemark.cli.add.TemplatesContainer') as mock_container_class,
                patch('prosemark.cli.add._create_add_node_interactor_with_console') as mock_interactor_factory,
                patch('prosemark.cli.add._write_template_content_to_node'),
            ):
                mock_container = MagicMock()
                mock_container_class.return_value = mock_container

                mock_use_case = MagicMock()
                mock_container.create_from_template_use_case = mock_use_case
                mock_use_case.create_single_template.return_value = {'success': True, 'content': 'Template content'}

                mock_interactor = MagicMock()
                mock_interactor_factory.return_value = mock_interactor
                mock_interactor.execute.return_value = 'node-abc-123'

                result = runner.invoke(add_command, ['New Node', '--template', 'example'])

                assert result.exit_code == 0
                assert 'Created files: node-abc-123.md, node-abc-123.notes.md' in result.output
                assert 'Updated binder structure' in result.output


class TestCLIAddDirectoryTemplateCoverage:
    """Test directory template handling (lines 233-241)."""

    def test_create_nodes_from_directory_template_single_file(self) -> None:
        """Test directory template with single file (lines 233-235)."""
        runner = CliRunner()

        with runner.isolated_filesystem():
            # Initialize project
            from prosemark.cli import init_command

            init_result = runner.invoke(init_command, ['--title', 'Test Project'])
            assert init_result.exit_code == 0

            templates_dir = Path('templates')
            templates_dir.mkdir()

            # Mock template system for directory template with single file
            with patch('prosemark.cli.add.TemplatesContainer') as mock_container_class:
                mock_container = MagicMock()
                mock_container_class.return_value = mock_container

                mock_use_case = MagicMock()
                mock_container.create_from_template_use_case = mock_use_case
                # Single template fails
                mock_use_case.create_single_template.return_value = {'success': False}
                # Directory template succeeds with single file
                mock_use_case.create_directory_template.return_value = {
                    'success': True,
                    'content': {'file1.md': 'Content 1'},
                    'file_count': 1,
                }

                # Mock node creation
                with (
                    patch('prosemark.cli.add._create_add_node_interactor_with_console') as mock_interactor_factory,
                    patch('prosemark.cli.add._write_template_content_to_node'),
                ):
                    mock_interactor = MagicMock()
                    mock_interactor_factory.return_value = mock_interactor
                    mock_interactor.execute.return_value = 'node-123'

                    result = runner.invoke(add_command, ['New Node', '--template', 'chapter'])

                    assert result.exit_code == 0
                    # Should not show multi-file note for single file
                    assert 'Only first file used' not in result.output

    def test_create_nodes_from_directory_template_multiple_files(self) -> None:
        """Test directory template with multiple files (lines 237-241)."""
        runner = CliRunner()

        with runner.isolated_filesystem():
            # Initialize project
            from prosemark.cli import init_command

            init_result = runner.invoke(init_command, ['--title', 'Test Project'])
            assert init_result.exit_code == 0

            templates_dir = Path('templates')
            templates_dir.mkdir()

            # Mock template system for directory template with multiple files
            with patch('prosemark.cli.add.TemplatesContainer') as mock_container_class:
                mock_container = MagicMock()
                mock_container_class.return_value = mock_container

                mock_use_case = MagicMock()
                mock_container.create_from_template_use_case = mock_use_case
                # Single template fails
                mock_use_case.create_single_template.return_value = {'success': False}
                # Directory template succeeds with multiple files
                mock_use_case.create_directory_template.return_value = {
                    'success': True,
                    'content': {'file1.md': 'Content 1', 'file2.md': 'Content 2', 'file3.md': 'Content 3'},
                    'file_count': 3,
                }

                # Mock node creation
                with (
                    patch('prosemark.cli.add._create_add_node_interactor_with_console') as mock_interactor_factory,
                    patch('prosemark.cli.add._write_template_content_to_node'),
                ):
                    mock_interactor = MagicMock()
                    mock_interactor_factory.return_value = mock_interactor
                    mock_interactor.execute.return_value = 'node-123'

                    result = runner.invoke(add_command, ['New Node', '--template', 'chapter'])

                    assert result.exit_code == 0
                    # Should show multi-file note
                    assert 'Directory template had 3 files' in result.output
                    assert 'Only first file used for node content' in result.output


class TestCLIAddWriteTemplateContentCoverage:
    """Test writing template content to node files (lines 246-272)."""

    def test_write_template_content_with_frontmatter(self) -> None:
        """Test writing template content to node with existing frontmatter (lines 253-260)."""
        runner = CliRunner()

        with runner.isolated_filesystem():
            # Initialize project
            from prosemark.cli import init_command

            init_result = runner.invoke(init_command, ['--title', 'Test Project'])
            assert init_result.exit_code == 0

            # Create a node file with frontmatter
            node_file = Path('node-123.md')
            node_file.write_text('---\ntitle: "Original Title"\n---\n\nOriginal body', encoding='utf-8')

            templates_dir = Path('templates')
            templates_dir.mkdir()

            # Mock template system to trigger write with existing frontmatter
            with patch('prosemark.cli.add.TemplatesContainer') as mock_container_class:
                mock_container = MagicMock()
                mock_container_class.return_value = mock_container

                mock_use_case = MagicMock()
                mock_container.create_from_template_use_case = mock_use_case
                mock_use_case.create_single_template.return_value = {'success': True, 'content': 'New template content'}

                # Mock node creation to return our test node
                with patch('prosemark.cli.add._create_add_node_interactor_with_console') as mock_interactor_factory:
                    mock_interactor = MagicMock()
                    mock_interactor_factory.return_value = mock_interactor
                    mock_interactor.execute.return_value = 'node-123'

                    result = runner.invoke(add_command, ['New Node', '--template', 'example'])

                    assert result.exit_code == 0

                    # Verify frontmatter was preserved
                    content = node_file.read_text(encoding='utf-8')
                    assert '---\ntitle: "Original Title"\n---' in content
                    assert 'New template content' in content

    def test_write_template_content_malformed_frontmatter(self) -> None:
        """Test writing template content with malformed frontmatter (lines 261-263)."""
        runner = CliRunner()

        with runner.isolated_filesystem():
            # Initialize project
            from prosemark.cli import init_command

            init_result = runner.invoke(init_command, ['--title', 'Test Project'])
            assert init_result.exit_code == 0

            # Create a node file with malformed frontmatter (only one ---)
            node_file = Path('node-456.md')
            node_file.write_text('---\nmalformed\nOriginal body', encoding='utf-8')

            templates_dir = Path('templates')
            templates_dir.mkdir()

            # Mock template system
            with patch('prosemark.cli.add.TemplatesContainer') as mock_container_class:
                mock_container = MagicMock()
                mock_container_class.return_value = mock_container

                mock_use_case = MagicMock()
                mock_container.create_from_template_use_case = mock_use_case
                mock_use_case.create_single_template.return_value = {'success': True, 'content': 'New content'}

                # Mock node creation to return our test node
                with patch('prosemark.cli.add._create_add_node_interactor_with_console') as mock_interactor_factory:
                    mock_interactor = MagicMock()
                    mock_interactor_factory.return_value = mock_interactor
                    mock_interactor.execute.return_value = 'node-456'

                    result = runner.invoke(add_command, ['New Node', '--template', 'example'])

                    assert result.exit_code == 0

                    # Verify content was appended to malformed frontmatter
                    content = node_file.read_text(encoding='utf-8')
                    assert 'New content' in content

    def test_write_template_content_no_frontmatter(self) -> None:
        """Test writing template content when no frontmatter exists (lines 264-266)."""
        runner = CliRunner()

        with runner.isolated_filesystem():
            # Initialize project
            from prosemark.cli import init_command

            init_result = runner.invoke(init_command, ['--title', 'Test Project'])
            assert init_result.exit_code == 0

            # Create a node file with no frontmatter
            node_file = Path('node-789.md')
            node_file.write_text('Just plain content, no frontmatter', encoding='utf-8')

            templates_dir = Path('templates')
            templates_dir.mkdir()

            # Mock template system
            with patch('prosemark.cli.add.TemplatesContainer') as mock_container_class:
                mock_container = MagicMock()
                mock_container_class.return_value = mock_container

                mock_use_case = MagicMock()
                mock_container.create_from_template_use_case = mock_use_case
                mock_use_case.create_single_template.return_value = {'success': True, 'content': 'Template content'}

                # Mock node creation to return our test node
                with patch('prosemark.cli.add._create_add_node_interactor_with_console') as mock_interactor_factory:
                    mock_interactor = MagicMock()
                    mock_interactor_factory.return_value = mock_interactor
                    mock_interactor.execute.return_value = 'node-789'

                    result = runner.invoke(add_command, ['New Node', '--template', 'example'])

                    assert result.exit_code == 0

                    # Verify content was replaced (no frontmatter to preserve)
                    content = node_file.read_text(encoding='utf-8')
                    assert content == 'Template content'

    def test_write_template_content_file_error(self) -> None:
        """Test writing template content with file system error (lines 271-272)."""
        runner = CliRunner()

        with runner.isolated_filesystem():
            # Initialize project
            from prosemark.cli import init_command

            init_result = runner.invoke(init_command, ['--title', 'Test Project'])
            assert init_result.exit_code == 0

            templates_dir = Path('templates')
            templates_dir.mkdir()

            # Mock template system
            with patch('prosemark.cli.add.TemplatesContainer') as mock_container_class:
                mock_container = MagicMock()
                mock_container_class.return_value = mock_container

                mock_use_case = MagicMock()
                mock_container.create_from_template_use_case = mock_use_case
                mock_use_case.create_single_template.return_value = {'success': True, 'content': 'Content'}

                # Mock node creation and file write to trigger error
                with (
                    patch('prosemark.cli.add._create_add_node_interactor_with_console') as mock_interactor_factory,
                    patch('pathlib.Path.read_text') as mock_read,
                ):
                    mock_interactor = MagicMock()
                    mock_interactor_factory.return_value = mock_interactor
                    mock_interactor.execute.return_value = 'node-999'

                    # Simulate read error
                    mock_read.side_effect = OSError('Permission denied')

                    result = runner.invoke(add_command, ['New Node', '--template', 'example'])

                    assert result.exit_code == 1
                    # Message format: "Error writing template content: Permission denied"
                    assert 'Error writing template content' in result.output
