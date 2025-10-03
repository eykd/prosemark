"""Main CLI entry point for prosemark.

This module provides the main command-line interface for the prosemark
writing project manager. It uses Typer for type-safe CLI generation
and delegates all business logic to use case interactors.
"""

# Standard library imports
from collections.abc import Callable
from pathlib import Path
from typing import Annotated, Any, Protocol

# Third-party imports
import typer

# Adapter imports
from prosemark.adapters.binder_repo_fs import BinderRepoFs
from prosemark.adapters.clock_system import ClockSystem
from prosemark.adapters.console_pretty import ConsolePretty
from prosemark.adapters.editor_launcher_system import EditorLauncherSystem
from prosemark.adapters.id_generator_uuid7 import IdGeneratorUuid7
from prosemark.adapters.logger_stdout import LoggerStdout
from prosemark.adapters.node_repo_fs import NodeRepoFs

# Use case imports
from prosemark.app.materialize_all_placeholders import MaterializeAllPlaceholders
from prosemark.app.materialize_node import MaterializeNode
from prosemark.app.materialize_node import MaterializeNode as MaterializeNodeUseCase
from prosemark.app.use_cases import (
    AddNode,
    AuditBinder,
    EditPart,
    InitProject,
    MoveNode,
    RemoveNode,
    ShowStructure,
)
from prosemark.domain.batch_materialize_result import BatchMaterializeResult

# Domain model imports
from prosemark.domain.binder import Item
from prosemark.domain.models import BinderItem, NodeId

# Exception imports
from prosemark.exceptions import (
    BinderFormatError,
    BinderIntegrityError,
    BinderNotFoundError,
    EditorLaunchError,
    FileSystemError,
    NodeIdentityError,
    NodeNotFoundError,
    PlaceholderNotFoundError,
)

# Freewriting imports
from prosemark.freewriting.container import run_freewriting_session

# Port imports
from prosemark.ports.config_port import ConfigPort, ProsemarkConfig


# Protocol definitions
class MaterializationResult(Protocol):
    """Protocol for materialization process result objects.

    Defines the expected interface for results of materialization operations,
    capturing details about the process such as placeholders materialized,
    failures encountered, and execution metadata.
    """

    total_placeholders: int
    successful_materializations: list[Any]
    failed_materializations: list[Any]
    has_failures: bool
    type: str | None
    is_complete_success: bool
    execution_time: float
    message: str | None
    summary_message: Callable[[], str]


app = typer.Typer(
    name='pmk',
    help='Prosemark CLI - A hierarchical writing project manager',
    add_completion=False,
)

# Alias for backward compatibility with tests
cli = app


class FileSystemConfigPort(ConfigPort):
    """Temporary config port implementation."""

    def create_default_config(self, config_path: Path) -> None:
        """Create default configuration file."""
        # For MVP, we don't need a config file

    @staticmethod
    def config_exists(config_path: Path) -> bool:
        """Check if configuration file already exists."""
        return config_path.exists()

    @staticmethod
    def get_default_config_values() -> ProsemarkConfig:
        """Return default configuration values as dictionary."""
        return {}

    @staticmethod
    def load_config(_config_path: Path) -> dict[str, Any]:
        """Load configuration from file."""
        return {}


def _get_project_root() -> Path:
    """Get the current project root directory."""
    return Path.cwd()


@app.command()
def init(
    title: Annotated[str, typer.Option('--title', '-t', help='Project title')],
    path: Annotated[Path | None, typer.Option('--path', '-p', help='Project directory')] = None,
) -> None:
    """Initialize a new prosemark project."""
    try:
        project_path = path or Path.cwd()

        # Wire up dependencies
        binder_repo = BinderRepoFs(project_path)
        config_port = FileSystemConfigPort()
        console_port = ConsolePretty()
        logger = LoggerStdout()
        clock = ClockSystem()

        # Execute use case
        interactor = InitProject(
            binder_repo=binder_repo,
            config_port=config_port,
            console_port=console_port,
            logger=logger,
            clock=clock,
        )
        interactor.execute(project_path)

        # Success output matching test expectations
        typer.echo(f'Project "{title}" initialized successfully')
        typer.echo('Created _binder.md with project structure')

    except BinderIntegrityError:
        typer.echo('Error: Directory already contains a prosemark project', err=True)
        raise typer.Exit(1) from None
    except FileSystemError as e:
        typer.echo(f'Error: {e}', err=True)
        raise typer.Exit(2) from e
    except Exception as e:
        typer.echo(f'Unexpected error: {e}', err=True)
        raise typer.Exit(3) from e


@app.command()
def add(
    title: Annotated[str, typer.Argument(help='Display title for the new node')],
    parent: Annotated[str | None, typer.Option('--parent', help='Parent node ID')] = None,
    position: Annotated[int | None, typer.Option('--position', help="Position in parent's children")] = None,
    path: Annotated[Path | None, typer.Option('--path', '-p', help='Project directory')] = None,
) -> None:
    """Add a new node to the binder hierarchy."""
    try:
        project_root = path or _get_project_root()

        # Wire up dependencies
        binder_repo = BinderRepoFs(project_root)
        clock = ClockSystem()
        editor_port = EditorLauncherSystem()
        node_repo = NodeRepoFs(project_root, editor_port, clock)
        id_generator = IdGeneratorUuid7()
        logger = LoggerStdout()

        # Execute use case
        interactor = AddNode(
            binder_repo=binder_repo,
            node_repo=node_repo,
            id_generator=id_generator,
            logger=logger,
            clock=clock,
        )

        parent_id = NodeId(parent) if parent else None
        node_id = interactor.execute(
            title=title,
            synopsis=None,
            parent_id=parent_id,
            position=position,
        )

        # Success output
        typer.echo(f'Added "{title}" ({node_id})')
        typer.echo(f'Created files: {node_id}.md, {node_id}.notes.md')
        typer.echo('Updated binder structure')

    except NodeNotFoundError:
        typer.echo('Error: Parent node not found', err=True)
        raise typer.Exit(1) from None
    except ValueError:
        typer.echo('Error: Invalid position index', err=True)
        raise typer.Exit(2) from None
    except FileSystemError as e:
        typer.echo(f'Error: File creation failed - {e}', err=True)
        raise typer.Exit(3) from e


@app.command()
def edit(
    node_id: Annotated[str, typer.Argument(help='Node identifier')],
    part: Annotated[str, typer.Option('--part', help='Content part to edit')] = 'draft',
    path: Annotated[Path | None, typer.Option('--path', '-p', help='Project directory')] = None,
) -> None:
    """Open node content in your preferred editor."""
    try:
        project_root = path or _get_project_root()

        # Wire up dependencies
        binder_repo = BinderRepoFs(project_root)
        clock = ClockSystem()
        editor_port = EditorLauncherSystem()
        node_repo = NodeRepoFs(project_root, editor_port, clock)
        logger = LoggerStdout()

        # Execute use case
        interactor = EditPart(
            binder_repo=binder_repo,
            node_repo=node_repo,
            logger=logger,
        )

        interactor.execute(NodeId(node_id), part)

        # Success output
        if part == 'draft':
            typer.echo(f'Opened {node_id}.md in editor')
        elif part == 'notes':
            typer.echo(f'Opened {node_id}.notes.md in editor')
        else:
            typer.echo(f'Opened {part} for {node_id} in editor')

    except NodeNotFoundError:
        typer.echo('Error: Node not found', err=True)
        raise typer.Exit(1) from None
    except EditorLaunchError:
        typer.echo('Error: Editor not available', err=True)
        raise typer.Exit(2) from None
    except FileSystemError:
        typer.echo('Error: File permission denied', err=True)
        raise typer.Exit(3) from None
    except ValueError as e:
        typer.echo(f'Error: {e}', err=True)
        raise typer.Exit(1) from e


def _output_structure_as_json(binder_repo: BinderRepoFs, parsed_node_id: NodeId | None) -> None:
    """Output structure in JSON format."""
    import json

    binder = binder_repo.load()

    def item_to_dict(item: Item | BinderItem) -> dict[str, Any]:
        result: dict[str, Any] = {
            'display_title': item.display_title,
        }
        node_id = item.id if hasattr(item, 'id') else (item.node_id if hasattr(item, 'node_id') else None)
        if node_id:
            result['node_id'] = str(node_id)
        item_children = item.children if hasattr(item, 'children') else []
        if item_children:
            result['children'] = [item_to_dict(child) for child in item_children]
        return result

    if parsed_node_id is None:
        # Full tree
        data: dict[str, list[dict[str, Any]]] = {'roots': [item_to_dict(item) for item in binder.roots]}
    else:
        # Subtree - find the specific node
        target_item = binder.find_by_id(parsed_node_id)
        if target_item is None:
            typer.echo(f'Error: Node not found in binder: {parsed_node_id}', err=True)
            raise typer.Exit(1)
        data = {'roots': [item_to_dict(target_item)]}

    typer.echo(json.dumps(data, indent=2))


@app.command()
def structure(
    node_id: Annotated[str | None, typer.Argument(help='Node ID to display as subtree root')] = None,
    output_format: Annotated[str, typer.Option('--format', '-f', help='Output format')] = 'tree',
    path: Annotated[Path | None, typer.Option('--path', '-p', help='Project directory')] = None,
) -> None:
    """Display project hierarchy.

    If NODE_ID is provided, only show the subtree starting from that node.
    """
    try:
        project_root = path or _get_project_root()

        # Wire up dependencies
        binder_repo = BinderRepoFs(project_root)
        logger = LoggerStdout()

        # Parse and validate node_id if provided
        parsed_node_id = None
        if node_id is not None:
            parsed_node_id = NodeId(node_id)

        # Execute use case
        interactor = ShowStructure(
            binder_repo=binder_repo,
            logger=logger,
        )

        structure_str = interactor.execute(node_id=parsed_node_id)

        if output_format == 'tree':
            typer.echo('Project Structure:')
            typer.echo(structure_str)
        elif output_format == 'json':
            _output_structure_as_json(binder_repo, parsed_node_id)
        else:
            typer.echo(f"Error: Unknown format '{output_format}'", err=True)
            raise typer.Exit(1)

    except NodeNotFoundError as e:
        typer.echo(f'Error: {e}', err=True)
        raise typer.Exit(1) from e
    except (ValueError, NodeIdentityError) as e:
        # Invalid node ID format
        typer.echo(f'Error: Invalid node ID format: {e}', err=True)
        raise typer.Exit(1) from e
    except FileSystemError as e:
        typer.echo(f'Error: {e}', err=True)
        raise typer.Exit(1) from e


@app.command()
def write(
    node_uuid: Annotated[str | None, typer.Argument(help='UUID of target node (optional)')] = None,
    title: Annotated[str | None, typer.Option('--title', '-t', help='Session title')] = None,
    word_count_goal: Annotated[int | None, typer.Option('--words', '-w', help='Word count goal')] = None,
    time_limit: Annotated[int | None, typer.Option('--time', help='Time limit in minutes')] = None,
    path: Annotated[Path | None, typer.Option('--path', '-p', help='Project directory')] = None,
) -> None:
    """Start a freewriting session in a distraction-free TUI."""
    try:
        project_root = path or _get_project_root()

        # Run freewriting session with dependency injection
        run_freewriting_session(
            node_uuid=node_uuid,
            title=title,
            word_count_goal=word_count_goal,
            time_limit=time_limit,
            project_path=project_root,
        )

    except Exception as e:
        typer.echo(f'Error: {e}', err=True)
        raise typer.Exit(1) from e


def _validate_materialize_args(title: str | None, *, all_placeholders: bool) -> None:
    """Validate mutual exclusion of materialize arguments."""
    if title and all_placeholders:
        typer.echo("Error: Cannot specify both 'title' and '--all' options", err=True)
        raise typer.Exit(1) from None

    if not title and not all_placeholders:
        typer.echo("Error: Must specify either placeholder 'title' or '--all' flag", err=True)
        raise typer.Exit(1) from None


def _create_shared_dependencies(
    project_root: Path,
) -> tuple[BinderRepoFs, ClockSystem, EditorLauncherSystem, NodeRepoFs, IdGeneratorUuid7, LoggerStdout]:
    """Create shared dependencies for materialization operations."""
    binder_repo = BinderRepoFs(project_root)
    clock = ClockSystem()
    editor_port = EditorLauncherSystem()
    node_repo = NodeRepoFs(project_root, editor_port, clock)
    id_generator = IdGeneratorUuid7()
    logger = LoggerStdout()
    return binder_repo, clock, editor_port, node_repo, id_generator, logger


def _generate_json_result(result: MaterializationResult | BatchMaterializeResult, output_type: str) -> dict[str, Any]:
    """Generate JSON result dictionary for materialization process."""
    json_result: dict[str, Any] = {
        'type': output_type,
        'total_placeholders': result.total_placeholders,
        'successful_materializations': len(result.successful_materializations),
        'failed_materializations': len(result.failed_materializations),
        'execution_time': result.execution_time,
    }

    # Add overall message
    if result.total_placeholders == 0:
        json_result['message'] = 'No placeholders found in binder'
    elif len(result.failed_materializations) == 0:
        json_result['message'] = f'Successfully materialized all {result.total_placeholders} placeholders'
    else:
        success_count = len(result.successful_materializations)
        failure_count = len(result.failed_materializations)
        json_result['message'] = (
            f'Materialized {success_count} of {result.total_placeholders} placeholders ({failure_count} failures)'
        )

    # Add results based on type
    if output_type == 'batch_partial':
        json_result['successes'] = [
            {'placeholder_title': success.display_title, 'node_id': str(success.node_id.value)}
            for success in result.successful_materializations
        ]
        json_result['failures'] = [
            {
                'placeholder_title': failure.display_title,
                'error_type': failure.error_type,
                'error_message': failure.error_message,
            }
            for failure in result.failed_materializations
        ]
    elif result.successful_materializations or result.failed_materializations:
        details_list: list[dict[str, str]] = []
        details_list.extend(
            {
                'placeholder_title': success.display_title,
                'node_id': str(success.node_id.value),
                'status': 'success',
            }
            for success in result.successful_materializations
        )

        details_list.extend(
            {
                'placeholder_title': failure.display_title,
                'error_type': failure.error_type,
                'error_message': failure.error_message,
                'status': 'failed',
            }
            for failure in result.failed_materializations
        )

        json_result['details'] = details_list

    return json_result


def _check_result_failure_status(
    result: MaterializationResult | BatchMaterializeResult, *, continue_on_error: bool = False
) -> None:
    """Check and handle result failure status."""
    has_failures = len(result.failed_materializations) > 0

    if has_failures:
        if not continue_on_error:
            raise typer.Exit(1) from None
        if len(result.successful_materializations) == 0:
            raise typer.Exit(1) from None


def _report_materialization_progress(
    result: MaterializationResult | BatchMaterializeResult,
    *,
    json_output: bool = False,
    progress_messages: list[str] | None = None,
) -> None:
    """Report materialization progress with human-readable or JSON output."""
    progress_messages = progress_messages or []
    if not json_output and not progress_messages:
        if result.total_placeholders == 0:
            typer.echo('No placeholders found to materialize')
        else:
            typer.echo(f'Found {result.total_placeholders} placeholders to materialize')
            for success in result.successful_materializations:
                typer.echo(f"✓ Materialized '{success.display_title}'")
            for failure in result.failed_materializations:
                typer.echo(f"✗ Failed to materialize '{failure.display_title}'")
                typer.echo(failure.error_message)


def _materialize_all_placeholders(
    project_root: Path,
    binder_repo: BinderRepoFs,
    node_repo: NodeRepoFs,
    id_generator: IdGeneratorUuid7,
    clock: ClockSystem,
    logger: LoggerStdout,
    *,
    json_output: bool = False,
    continue_on_error: bool = False,
) -> None:
    """Execute batch materialization of all placeholders."""
    console = ConsolePretty()

    # Create individual materialize use case for delegation
    materialize_node_use_case = MaterializeNode(
        binder_repo=binder_repo,
        node_repo=node_repo,
        id_generator=id_generator,
        clock=clock,
        console=console,
        logger=logger,
    )

    # Create batch use case
    batch_interactor = MaterializeAllPlaceholders(
        materialize_node_use_case=materialize_node_use_case,
        binder_repo=binder_repo,
        node_repo=node_repo,
        id_generator=id_generator,
        clock=clock,
        logger=logger,
    )

    # Execute with progress callback and track messages
    progress_messages: list[str] = []

    def progress_callback(message: str) -> None:
        progress_messages.append(message)
        typer.echo(message)

    result = batch_interactor.execute(
        project_path=project_root,
        progress_callback=progress_callback,
    )

    # Report progress messages
    _report_materialization_progress(result, json_output=json_output, progress_messages=progress_messages)

    # Report final results
    if json_output:
        import json

        # Determine type based on results
        output_type: str = 'batch_partial' if result.failed_materializations else 'batch'
        json_result = _generate_json_result(result, output_type)
        typer.echo(json.dumps(json_result, indent=2))

        # Check for specific interruption types
        result_type: str | None = getattr(result, 'type', None)
        if result_type in {'batch_interrupted', 'batch_critical_failure'}:
            raise typer.Exit(1) from None

        # Handle failures
        _check_result_failure_status(result, continue_on_error=continue_on_error)
    else:
        if result.total_placeholders == 0:
            return

        result_type = getattr(result, 'type', None)
        if result_type in {'batch_interrupted', 'batch_critical_failure'}:
            raise typer.Exit(1) from None

        success_count = len(result.successful_materializations)
        _describe_materialization_result(result, success_count, continue_on_error=continue_on_error)


def _describe_materialization_result(
    result: MaterializationResult | BatchMaterializeResult, success_count: int, *, continue_on_error: bool = False
) -> None:
    """Describe materialization results with appropriate messaging."""
    is_complete_success = len(result.failed_materializations) == 0 and result.total_placeholders > 0

    if is_complete_success:
        typer.echo(f'Successfully materialized all {result.total_placeholders} placeholders')
    else:
        # Retrieve or generate summary message
        summary_msg = _get_summary_message(result, success_count)
        typer.echo(summary_msg)

        # Check for interrupted operations
        _check_result_failure_status(result, continue_on_error=continue_on_error)


def _get_safe_attribute(
    result: MaterializationResult | BatchMaterializeResult, attr_name: str, default: str = ''
) -> str:
    """Safely retrieve an attribute from a result object."""
    try:
        value = getattr(result, attr_name, default)
        if callable(value):
            value_result = value()
            return value_result if isinstance(value_result, str) else default
        return value if isinstance(value, str) else default
    except (TypeError, ValueError, AttributeError):
        return default


def _get_summary_message(result: MaterializationResult | BatchMaterializeResult, success_count: int) -> str:
    """Get summary message for materialization results."""
    # First try standard message retrieval methods
    summary_msg = _get_safe_attribute(result, 'message')
    if not summary_msg:
        summary_msg = _get_safe_attribute(result, 'summary_message')

    # If no standard method works, generate a manual summary
    if not summary_msg:
        failure_count = len(result.failed_materializations)
        if failure_count == 1:
            summary_msg = (
                f'Materialized {success_count} of {result.total_placeholders} placeholders ({failure_count} failure)'
            )
        else:
            summary_msg = (
                f'Materialized {success_count} of {result.total_placeholders} placeholders ({failure_count} failures)'
            )

    return summary_msg


def _materialize_single_placeholder(
    title: str,
    binder_repo: BinderRepoFs,
    node_repo: NodeRepoFs,
    id_generator: IdGeneratorUuid7,
    clock: ClockSystem,
    console: ConsolePretty,
    logger: LoggerStdout,
) -> None:
    """Execute single materialization."""
    interactor = MaterializeNodeUseCase(
        binder_repo=binder_repo,
        node_repo=node_repo,
        id_generator=id_generator,
        clock=clock,
        console=console,
        logger=logger,
    )

    result = interactor.execute(title=title)

    # Only output success messages if it was newly materialized
    if not result.was_already_materialized:
        typer.echo(f'Materialized "{title}" ({result.node_id})')
        typer.echo(f'Created files: {result.node_id}.md, {result.node_id}.notes.md')
        typer.echo('Updated binder structure')


@app.command()
def materialize(
    title: Annotated[str | None, typer.Argument(help='Display title of placeholder to materialize')] = None,
    all_placeholders: Annotated[bool, typer.Option('--all', help='Materialize all placeholders in binder')] = False,  # noqa: FBT002
    _parent: Annotated[str | None, typer.Option('--parent', help='Parent node ID to search within')] = None,
    json_output: Annotated[bool, typer.Option('--json', help='Output results in JSON format')] = False,  # noqa: FBT002
    path: Annotated[Path | None, typer.Option('--path', '-p', help='Project directory')] = None,
) -> None:
    """Convert placeholder(s) to actual nodes."""
    try:
        _validate_materialize_args(title, all_placeholders=all_placeholders)
        project_root = path or _get_project_root()
        binder_repo, clock, _editor_port, node_repo, id_generator, logger = _create_shared_dependencies(project_root)
        console = ConsolePretty()

        if all_placeholders:
            _materialize_all_placeholders(
                project_root, binder_repo, node_repo, id_generator, clock, logger, json_output=json_output
            )
        else:
            # Ensure title is not None for type safety
            if title is None:
                typer.echo('Error: Title is required for single materialization', err=True)
                raise typer.Exit(1) from None
            _materialize_single_placeholder(title, binder_repo, node_repo, id_generator, clock, console, logger)

    except PlaceholderNotFoundError:
        typer.echo('Error: Placeholder not found', err=True)
        raise typer.Exit(1) from None
    except BinderFormatError as e:
        typer.echo(f'Error: Malformed binder structure - {e}', err=True)
        raise typer.Exit(1) from None
    except BinderNotFoundError:
        typer.echo('Error: Binder file not found - No _binder.md file in directory', err=True)
        raise typer.Exit(1) from None
    except FileSystemError:
        typer.echo('Error: File creation failed', err=True)
        raise typer.Exit(2) from None


@app.command()
def move(
    node_id: Annotated[str, typer.Argument(help='Node to move')],
    parent: Annotated[str | None, typer.Option('--parent', help='New parent node')] = None,
    position: Annotated[int | None, typer.Option('--position', help="Position in new parent's children")] = None,
    path: Annotated[Path | None, typer.Option('--path', '-p', help='Project directory')] = None,
) -> None:
    """Reorganize binder hierarchy."""
    try:
        project_root = path or _get_project_root()

        # Wire up dependencies
        binder_repo = BinderRepoFs(project_root)
        logger = LoggerStdout()

        # Execute use case
        interactor = MoveNode(
            binder_repo=binder_repo,
            logger=logger,
        )

        parent_id = NodeId(parent) if parent else None
        interactor.execute(
            node_id=NodeId(node_id),
            parent_id=parent_id,
            position=position,
        )

        # Success output
        parent_str = 'root' if parent is None else f'parent {parent}'
        position_str = f' at position {position}' if position is not None else ''
        typer.echo(f'Moved node to {parent_str}{position_str}')
        typer.echo('Updated binder structure')

    except NodeNotFoundError as e:
        typer.echo(f'Error: {e}', err=True)
        raise typer.Exit(1) from e
    except ValueError:
        typer.echo('Error: Invalid parent or position', err=True)
        raise typer.Exit(2) from None
    except BinderIntegrityError:
        typer.echo('Error: Would create circular reference', err=True)
        raise typer.Exit(3) from None


@app.command()
def remove(
    node_id: Annotated[str, typer.Argument(help='Node to remove')],
    *,
    delete_files: Annotated[bool, typer.Option('--delete-files', help='Also delete node files')] = False,
    force: Annotated[bool, typer.Option('--force', '-f', help='Skip confirmation prompt')] = False,
    path: Annotated[Path | None, typer.Option('--path', '-p', help='Project directory')] = None,
) -> None:
    """Remove a node from the binder."""
    try:
        project_root = path or _get_project_root()

        # Confirmation prompt if not forced
        if not force and delete_files:
            confirm = typer.confirm(f'Really delete node {node_id} and its files?')
            if not confirm:
                typer.echo('Operation cancelled')
                raise typer.Exit(2)

        # Wire up dependencies
        binder_repo = BinderRepoFs(project_root)
        clock = ClockSystem()
        editor_port = EditorLauncherSystem()
        node_repo = NodeRepoFs(project_root, editor_port, clock)
        logger = LoggerStdout()

        # Execute use case
        interactor = RemoveNode(
            binder_repo=binder_repo,
            node_repo=node_repo,
            logger=logger,
        )

        # Get node title for output
        binder = binder_repo.load()
        target_item = binder.find_by_id(NodeId(node_id))
        title = target_item.display_title if target_item else node_id

        interactor.execute(NodeId(node_id), delete_files=delete_files)

        # Success output
        typer.echo(f'Removed "{title}" from binder')
        if delete_files:
            typer.echo(f'Deleted files: {node_id}.md, {node_id}.notes.md')
        else:
            typer.echo(f'Files preserved: {node_id}.md, {node_id}.notes.md')

    except NodeNotFoundError:
        typer.echo('Error: Node not found', err=True)
        raise typer.Exit(1) from None
    except FileSystemError:
        typer.echo('Error: File deletion failed', err=True)
        raise typer.Exit(3) from None


@app.command()
def audit(  # noqa: C901, PLR0912
    *,
    fix: Annotated[bool, typer.Option('--fix', help='Attempt to fix discovered issues')] = False,
    path: Annotated[Path | None, typer.Option('--path', '-p', help='Project directory')] = None,
) -> None:
    """Check project integrity."""
    try:
        project_root = path or _get_project_root()

        # Wire up dependencies
        binder_repo = BinderRepoFs(project_root)
        clock = ClockSystem()
        editor_port = EditorLauncherSystem()
        node_repo = NodeRepoFs(project_root, editor_port, clock)
        logger = LoggerStdout()

        # Execute use case
        interactor = AuditBinder(
            binder_repo=binder_repo,
            node_repo=node_repo,
            logger=logger,
        )

        report = interactor.execute()

        # Always report placeholders if they exist (informational)
        if report.placeholders:
            for placeholder in report.placeholders:
                typer.echo(f'⚠ PLACEHOLDER: "{placeholder.display_title}" (no associated files)')

        # Report actual issues if they exist
        has_real_issues = report.missing or report.orphans or report.mismatches
        if has_real_issues:
            if report.placeholders:
                typer.echo('')  # Add spacing after placeholders
            typer.echo('Project integrity issues found:')

            if report.missing:
                for missing in report.missing:
                    typer.echo(f'⚠ MISSING: Node {missing.node_id} referenced but files not found')

            if report.orphans:
                for orphan in report.orphans:
                    typer.echo(f'⚠ ORPHAN: File {orphan.file_path} exists but not in binder')

            if report.mismatches:
                for mismatch in report.mismatches:
                    typer.echo(f'⚠ MISMATCH: File {mismatch.file_path} ID mismatch')
        else:
            # Show success messages for real issues when none exist
            if report.placeholders:
                typer.echo('')  # Add spacing after placeholders
            typer.echo('Project integrity check completed')
            typer.echo('✓ All nodes have valid files')
            typer.echo('✓ All references are consistent')
            typer.echo('✓ No orphaned files found')

        # Only exit with error code for real issues, not placeholders
        if has_real_issues:
            if fix:
                typer.echo('\nNote: Auto-fix not implemented in MVP')
                raise typer.Exit(2)
            # Exit with code 1 when issues are found (standard audit behavior)
            raise typer.Exit(1)

    except FileSystemError as e:
        typer.echo(f'Error: {e}', err=True)
        raise typer.Exit(2) from e


def main() -> None:
    """Main entry point for the CLI."""
    app()


if __name__ == '__main__':  # pragma: no cover
    main()


@app.command(name='compile')
def compile_cmd(
    node_id: Annotated[str | None, typer.Argument(help='Node ID to compile. Omit to compile all root nodes.')] = None,
    path: Annotated[Path | None, typer.Option('--path', '-p', help='Project directory')] = None,
    include_empty: Annotated[  # noqa: FBT002
        bool, typer.Option('--include-empty', help='Include nodes with empty content')
    ] = False,
) -> None:
    """Compile a node subtree or all root nodes into concatenated plain text.

    If NODE_ID is provided, compiles that specific node and its descendants.
    If NODE_ID is omitted, compiles all materialized root nodes in binder order.
    """
    from prosemark.cli.compile import compile_command

    compile_command(node_id, path, include_empty=include_empty)
