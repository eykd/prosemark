"""CLI command for adding nodes to the binder."""

from pathlib import Path

import click

from prosemark.adapters.binder_repo_fs import BinderRepoFs
from prosemark.adapters.clock_system import ClockSystem
from prosemark.adapters.console_pretty import ConsolePretty
from prosemark.adapters.editor_launcher_system import EditorLauncherSystem
from prosemark.adapters.id_generator_uuid7 import IdGeneratorUuid7
from prosemark.adapters.logger_stdout import LoggerStdout
from prosemark.adapters.node_repo_fs import NodeRepoFs
from prosemark.app.use_cases import AddNode, InitProject
from prosemark.domain.models import NodeId
from prosemark.exceptions import FileSystemError, NodeNotFoundError
from prosemark.templates.container import TemplatesContainer
from prosemark.templates.domain.exceptions.template_exceptions import (
    TemplateNotFoundError as TemplateError,
)
from prosemark.templates.domain.exceptions.template_exceptions import (
    TemplateValidationError,
    UserCancelledError,
)

# Error handling constants
_INVALID_PARENT_EXIT_CODE = 1
_INVALID_POSITION_EXIT_CODE = 2
_FILE_SYSTEM_ERROR_EXIT_CODE = 3


@click.command()
@click.argument('title')
@click.option('--parent', help='Parent node ID')
@click.option('--position', type=int, help="Position in parent's children")
@click.option('--path', '-p', type=click.Path(path_type=Path), help='Project directory')
@click.option('--template', help='Create node from template')
@click.option('--list-templates', is_flag=True, help='List available templates')
def add_command(
    title: str,
    *,
    parent: str | None = None,
    position: int | None = None,
    path: Path | None = None,
    template: str | None = None,
    list_templates: bool = False,
) -> None:
    """Add a new node to the binder hierarchy, optionally from a template."""
    try:
        project_root = path or Path.cwd()

        # Handle template listing
        if list_templates:
            _handle_list_templates(project_root)
            return

        # Handle template creation
        if template:
            _handle_template_creation(template, title, parent, position, project_root)
            return

        # Auto-initialize project if it doesn't exist
        _ensure_project_initialized(project_root)

        # Execute use case
        interactor = _create_add_node_interactor(project_root)

        # Validate position if provided
        if position is not None and position < 0:
            _handle_invalid_position_error()

        parent_id = None
        if parent:
            try:
                parent_id = NodeId(parent)
            except ValueError as err:
                # Invalid parent ID format, treat as "parent not found"
                _handle_invalid_parent_error(err)
        node_id = interactor.execute(
            title=title,
            synopsis=None,
            parent_id=parent_id,
            position=position,
        )

        # Success output
        click.echo(f'Added "{title}" ({node_id})')
        click.echo(f'Created files: {node_id}.md, {node_id}.notes.md')
        click.echo('Updated binder structure')

    except NodeNotFoundError as err:
        _handle_node_not_found_error(err)
    except ValueError as err:
        _handle_invalid_position_error(err)
    except FileSystemError as err:
        _handle_file_system_error(err)


def _handle_list_templates(project_root: Path) -> None:
    """Handle listing available templates."""
    templates_dir = project_root / 'templates'
    if not templates_dir.exists():
        click.echo("No templates directory found. Create './templates' directory and add template files.")
        return

    try:
        container = TemplatesContainer(templates_dir)
        use_case = container.list_templates_use_case
        result = use_case.list_all_templates()

        if result['success']:
            total = result['total_templates']
            if total == 0:
                click.echo('No templates found in ./templates directory')
                return

            click.echo(f'Found {total} template(s):')

            # Single templates
            single_templates = result['single_templates']
            if single_templates['count'] > 0:
                click.echo('\nSingle templates:')
                for name in single_templates['names']:
                    click.echo(f'  - {name}')

            # Directory templates
            directory_templates = result['directory_templates']
            if directory_templates['count'] > 0:
                click.echo('\nDirectory templates:')
                for name in directory_templates['names']:
                    click.echo(f'  - {name}')
        else:
            _handle_template_listing_error(result.get('error', 'Unknown error'))

    except (TemplateError, TemplateValidationError, FileSystemError) as err:
        _handle_template_access_error(str(err))


def _handle_template_creation(
    template_name: str, title: str, parent: str | None, position: int | None, project_root: Path
) -> None:
    """Handle creating node from template."""
    templates_dir = project_root / 'templates'
    if not templates_dir.exists():
        click.echo("No templates directory found. Create './templates' directory and add template files.", err=True)
        raise SystemExit(1)

    try:
        # Initialize template system
        container = TemplatesContainer(templates_dir)
        create_use_case = container.create_from_template_use_case

        # Try single template first
        result = create_use_case.create_single_template(template_name)

        if result['success']:
            content = result['content']

            # Create node with template content
            _create_node_with_content(title, content, parent, position, project_root)

            click.echo(f'Created "{title}" from template "{template_name}"')
        else:
            # Try directory template
            result = create_use_case.create_directory_template(template_name)

            if result['success']:
                content_map = result['content']
                file_count = result['file_count']

                # Create multiple nodes from directory template
                _create_nodes_from_directory_template(title, content_map, parent, position, project_root)

                click.echo(f'Created "{title}" with {file_count} files from directory template "{template_name}"')
            else:
                error_type = result.get('error_type', 'Unknown')
                error_msg = result.get('error', 'Unknown error')
                _handle_template_creation_error(error_type, error_msg)

    except TemplateError:
        _handle_template_not_found_error(template_name)
    except TemplateValidationError as err:
        _handle_template_validation_error(str(err))
    except UserCancelledError:
        _handle_user_cancelled_error()
    except FileSystemError as err:
        _handle_template_processing_error(str(err))


def _create_node_with_content(
    title: str, content: str, parent: str | None, position: int | None, project_root: Path
) -> None:
    """Create a node with templated content."""
    # Auto-initialize project if it doesn't exist
    _ensure_project_initialized(project_root)

    # Wire up dependencies
    interactor = _create_add_node_interactor_with_console(project_root)

    # Validate position if provided
    if position is not None and position < 0:
        _handle_invalid_position_error()

    parent_id = None
    if parent:
        try:
            parent_id = NodeId(parent)
        except ValueError as err:
            _handle_invalid_parent_error(err)

    # Create node normally first
    node_id = interactor.execute(
        title=title,
        synopsis=None,
        parent_id=parent_id,
        position=position,
    )

    # Now write the template content to the node file
    _write_template_content_to_node(node_id, content, project_root)

    click.echo(f'Created files: {node_id}.md, {node_id}.notes.md')
    click.echo('Updated binder structure')


def _create_nodes_from_directory_template(
    title: str, content_map: dict[str, str], parent: str | None, position: int | None, project_root: Path
) -> None:
    """Create multiple nodes from directory template."""
    # This is a simplified implementation - creates main node with first file's content
    # In a full implementation, you might create child nodes for each file

    if content_map:
        first_content = next(iter(content_map.values()))
        _create_node_with_content(title, first_content, parent, position, project_root)

        # Could extend to create child nodes for additional files in content_map
        content_count = len(content_map)
        single_file = 1
        if content_count > single_file:
            click.echo(f'Note: Directory template had {content_count} files. Only first file used for node content.')


def _write_template_content_to_node(node_id: NodeId, content: str, project_root: Path) -> None:
    """Write template content to an existing node file."""
    node_file = project_root / f'{node_id}.md'

    try:
        # Read existing content to preserve frontmatter
        existing_content = node_file.read_text(encoding='utf-8')

        # Split into frontmatter and body
        frontmatter_separator = '---'
        frontmatter_parts_count = 3
        if existing_content.startswith(frontmatter_separator):
            parts = existing_content.split(frontmatter_separator, 2)
            if len(parts) >= frontmatter_parts_count:
                frontmatter = f'---{parts[1]}---'
                # Replace body with template content
                new_content = f'{frontmatter}\n\n{content}'
            else:
                # Malformed frontmatter, just append
                new_content = f'{existing_content}\n\n{content}'
        else:
            # No frontmatter, just replace content
            new_content = content

        # Write back to file
        node_file.write_text(new_content, encoding='utf-8')

    except (FileSystemError, OSError) as err:
        _handle_template_content_write_error(str(err))


# Utility functions to reduce local variables (PLR0914)


def _ensure_project_initialized(project_root: Path) -> None:
    """Ensure project is initialized, create if it doesn't exist."""
    binder_path = project_root / '_binder.md'
    if not binder_path.exists():
        from prosemark.cli.init import FileSystemConfigPort

        binder_repo_init = BinderRepoFs(project_root)
        config_port = FileSystemConfigPort()
        console_port = ConsolePretty()
        logger_init = LoggerStdout()
        clock_init = ClockSystem()

        init_interactor = InitProject(
            binder_repo=binder_repo_init,
            config_port=config_port,
            console_port=console_port,
            logger=logger_init,
            clock=clock_init,
        )
        init_interactor.execute(project_root)


def _create_add_node_interactor(project_root: Path) -> AddNode:
    """Create AddNode interactor with dependencies."""
    binder_repo = BinderRepoFs(project_root)
    clock = ClockSystem()
    editor = EditorLauncherSystem()
    node_repo = NodeRepoFs(project_root, editor, clock)
    id_generator = IdGeneratorUuid7()
    logger = LoggerStdout()

    return AddNode(
        binder_repo=binder_repo,
        node_repo=node_repo,
        id_generator=id_generator,
        logger=logger,
        clock=clock,
    )


def _create_add_node_interactor_with_console(project_root: Path) -> AddNode:
    """Create AddNode interactor with dependencies (console not needed)."""
    binder_repo = BinderRepoFs(project_root)
    clock = ClockSystem()
    editor = EditorLauncherSystem()
    node_repo = NodeRepoFs(project_root, editor, clock)
    id_generator = IdGeneratorUuid7()
    logger = LoggerStdout()

    return AddNode(
        binder_repo=binder_repo,
        node_repo=node_repo,
        id_generator=id_generator,
        logger=logger,
        clock=clock,
    )


# Error handling helper functions to address TRY301 and B904 issues


def _handle_invalid_position_error(err: ValueError | None = None) -> None:
    """Handle invalid position error."""
    click.echo('Error: Invalid position index', err=True)
    if err is not None:
        raise SystemExit(_INVALID_POSITION_EXIT_CODE) from err
    raise SystemExit(_INVALID_POSITION_EXIT_CODE)


def _handle_invalid_parent_error(err: ValueError) -> None:
    """Handle invalid parent node error."""
    click.echo('Error: Parent node not found', err=True)
    raise SystemExit(_INVALID_PARENT_EXIT_CODE) from err


def _handle_node_not_found_error(err: NodeNotFoundError) -> None:
    """Handle node not found error."""
    click.echo('Error: Parent node not found', err=True)
    raise SystemExit(_INVALID_PARENT_EXIT_CODE) from err


def _handle_file_system_error(err: FileSystemError) -> None:
    """Handle file system error."""
    click.echo(f'Error: File creation failed - {err}', err=True)
    raise SystemExit(_FILE_SYSTEM_ERROR_EXIT_CODE) from err


def _handle_template_listing_error(error_msg: str) -> None:
    """Handle template listing error."""
    click.echo(f'Error listing templates: {error_msg}', err=True)
    raise SystemExit(_INVALID_PARENT_EXIT_CODE)


def _handle_template_access_error(error_msg: str) -> None:
    """Handle template access error."""
    click.echo(f'Error accessing templates: {error_msg}', err=True)
    raise SystemExit(_INVALID_PARENT_EXIT_CODE)


def _handle_template_creation_error(error_type: str, error_msg: str) -> None:
    """Handle template creation error."""
    click.echo(f'Template error ({error_type}): {error_msg}', err=True)
    raise SystemExit(_INVALID_PARENT_EXIT_CODE)


def _handle_template_not_found_error(template_name: str) -> None:
    """Handle template not found error."""
    click.echo(f'Template "{template_name}" not found', err=True)
    raise SystemExit(_INVALID_PARENT_EXIT_CODE)


def _handle_template_validation_error(error_msg: str) -> None:
    """Handle template validation error."""
    click.echo(f'Template validation error: {error_msg}', err=True)
    raise SystemExit(_INVALID_PARENT_EXIT_CODE)


def _handle_user_cancelled_error() -> None:
    """Handle user cancelled error."""
    click.echo('Template creation cancelled by user')
    raise SystemExit(_INVALID_PARENT_EXIT_CODE)


def _handle_template_processing_error(error_msg: str) -> None:
    """Handle template processing error."""
    click.echo(f'Template processing error: {error_msg}', err=True)
    raise SystemExit(_INVALID_PARENT_EXIT_CODE)


def _handle_template_content_write_error(error_msg: str) -> None:
    """Handle template content write error."""
    click.echo(f'Error writing template content: {error_msg}', err=True)
    raise SystemExit(_INVALID_PARENT_EXIT_CODE)
