"""Main CLI entry point for prosemark.

This module provides the main command-line interface for the prosemark
writing project manager. It uses Typer for type-safe CLI generation
and delegates all business logic to use case interactors.
"""

from pathlib import Path
from typing import Annotated, Any

# Ensure this is imported early in the file
import typer

from prosemark.adapters.binder_repo_fs import BinderRepoFs
from prosemark.adapters.clock_system import ClockSystem
from prosemark.adapters.console_pretty import ConsolePretty
from prosemark.adapters.daily_repo_fs import DailyRepoFs
from prosemark.adapters.editor_launcher_system import EditorLauncherSystem
from prosemark.adapters.id_generator_uuid7 import IdGeneratorUuid7
from prosemark.adapters.logger_stdout import LoggerStdout
from prosemark.adapters.node_repo_fs import NodeRepoFs
from prosemark.app.use_cases import (
    AddNode,
    AuditBinder,
    EditPart,
    InitProject,
    MaterializeNode,
    MoveNode,
    RemoveNode,
    ShowStructure,
    WriteFreeform,
)
from prosemark.domain.binder import Item
from prosemark.domain.models import BinderItem, NodeId
from prosemark.exceptions import (
    AlreadyMaterializedError,
    BinderIntegrityError,
    EditorLaunchError,
    FileSystemError,
    NodeNotFoundError,
    PlaceholderNotFoundError,
)
from prosemark.ports.config_port import ConfigPort

app = typer.Typer(
    name='pmk',
    help='Prosemark CLI - A hierarchical writing project manager',
    add_completion=False,
)


class FileSystemConfigPort(ConfigPort):
    """Temporary config port implementation."""

    def create_default_config(self, config_path: Path) -> None:
        """Create default configuration file."""
        # For MVP, we don't need a config file

    def config_exists(self, config_path: Path) -> bool:
        """Check if configuration file already exists."""
        return config_path.exists()

    def get_default_config_values(self) -> dict[str, Any]:
        """Return default configuration values as dictionary."""
        return {}

    def load_config(self, _config_path: Path) -> dict[str, Any]:
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
) -> None:
    """Add a new node to the binder hierarchy."""
    try:
        project_root = _get_project_root()

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
) -> None:
    """Open node content in your preferred editor."""
    try:
        project_root = _get_project_root()

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


@app.command()
def structure(
    output_format: Annotated[str, typer.Option('--format', '-f', help='Output format')] = 'tree',
) -> None:
    """Display project hierarchy."""
    try:
        project_root = _get_project_root()

        # Wire up dependencies
        binder_repo = BinderRepoFs(project_root)
        logger = LoggerStdout()

        # Execute use case
        interactor = ShowStructure(
            binder_repo=binder_repo,
            logger=logger,
        )

        structure_str = interactor.execute()

        if output_format == 'tree':
            typer.echo('Project Structure:')
            typer.echo(structure_str)
        elif output_format == 'json':
            # For JSON format, we need to convert the tree to JSON
            # This is a simplified version for MVP
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

            data: dict[str, list[dict[str, Any]]] = {'roots': [item_to_dict(item) for item in binder.roots]}
            typer.echo(json.dumps(data, indent=2))
        else:
            typer.echo(f"Error: Unknown format '{output_format}'", err=True)
            raise typer.Exit(1)

    except FileSystemError as e:
        typer.echo(f'Error: {e}', err=True)
        raise typer.Exit(1) from e


@app.command()
def write(
    title: Annotated[str | None, typer.Argument(help='Optional title for freeform content')] = None,
) -> None:
    """Create a timestamped freeform writing file."""
    try:
        project_root = _get_project_root()

        # Wire up dependencies
        clock = ClockSystem()
        id_generator = IdGeneratorUuid7()
        daily_repo = DailyRepoFs(project_root, id_generator=id_generator, clock=clock)
        editor_port = EditorLauncherSystem()
        logger = LoggerStdout()

        # Execute use case
        interactor = WriteFreeform(
            daily_repo=daily_repo,
            editor_port=editor_port,
            logger=logger,
            clock=clock,
        )

        filename = interactor.execute(title)

        # Success output
        typer.echo(f'Created freeform file: {filename}')
        typer.echo('Opened in editor')

    except FileSystemError:
        typer.echo('Error: File creation failed', err=True)
        raise typer.Exit(1) from None
    except EditorLaunchError:
        typer.echo('Error: Editor launch failed', err=True)
        raise typer.Exit(2) from None


@app.command()
def materialize(
    title: Annotated[str, typer.Argument(help='Display title of placeholder to materialize')],
    _parent: Annotated[str | None, typer.Option('--parent', help='Parent node ID to search within')] = None,
) -> None:
    """Convert a placeholder to an actual node."""
    try:
        project_root = _get_project_root()

        # Wire up dependencies
        binder_repo = BinderRepoFs(project_root)
        clock = ClockSystem()
        editor_port = EditorLauncherSystem()
        node_repo = NodeRepoFs(project_root, editor_port, clock)
        id_generator = IdGeneratorUuid7()
        logger = LoggerStdout()

        # Execute use case
        interactor = MaterializeNode(
            binder_repo=binder_repo,
            node_repo=node_repo,
            id_generator=id_generator,
            logger=logger,
        )

        node_id = interactor.execute(display_title=title, synopsis=None)

        # Success output
        typer.echo(f'Materialized "{title}" ({node_id})')
        typer.echo(f'Created files: {node_id}.md, {node_id}.notes.md')
        typer.echo('Updated binder structure')

    except PlaceholderNotFoundError:
        typer.echo('Error: Placeholder not found', err=True)
        raise typer.Exit(1) from None
    except AlreadyMaterializedError:
        typer.echo(f"Error: '{title}' is already materialized", err=True)
        raise typer.Exit(1) from None
    except FileSystemError:
        typer.echo('Error: File creation failed', err=True)
        raise typer.Exit(2) from None


@app.command()
def move(
    node_id: Annotated[str, typer.Argument(help='Node to move')],
    parent: Annotated[str | None, typer.Option('--parent', help='New parent node')] = None,
    position: Annotated[int | None, typer.Option('--position', help="Position in new parent's children")] = None,
) -> None:
    """Reorganize binder hierarchy."""
    try:
        project_root = _get_project_root()

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
    delete_files: Annotated[bool, typer.Option('--delete-files', help='Also delete node files')] = False,  # noqa: FBT002
    force: Annotated[bool, typer.Option('--force', '-f', help='Skip confirmation prompt')] = False,  # noqa: FBT002
) -> None:
    """Remove a node from the binder."""
    try:
        project_root = _get_project_root()

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
def audit(  # noqa: C901
    fix: Annotated[bool, typer.Option('--fix', help='Attempt to fix discovered issues')] = False,  # noqa: FBT002
) -> None:
    """Check project integrity."""
    try:
        project_root = _get_project_root()

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

        if report.is_clean():
            typer.echo('Project integrity check completed')
            typer.echo('✓ All nodes have valid files')
            typer.echo('✓ All references are consistent')
            typer.echo('✓ No orphaned files found')
        else:
            typer.echo('Project integrity issues found:')

            if report.placeholders:
                for placeholder in report.placeholders:
                    typer.echo(f'⚠ PLACEHOLDER: "{placeholder.display_title}" (no associated files)')

            if report.missing:
                for missing in report.missing:
                    typer.echo(f'⚠ MISSING: Node {missing.node_id} referenced but files not found')

            if report.orphans:
                for orphan in report.orphans:
                    typer.echo(f'⚠ ORPHAN: File {orphan.file_path} exists but not in binder')

            if report.mismatches:
                for mismatch in report.mismatches:
                    typer.echo(f'⚠ MISMATCH: File {mismatch.file_path} ID mismatch')

            if fix:
                typer.echo('\nNote: Auto-fix not implemented in MVP')
                raise typer.Exit(2)
            raise typer.Exit(1)

    except FileSystemError as e:
        typer.echo(f'Error: {e}', err=True)
        raise typer.Exit(2) from e


def main() -> None:
    """Main entry point for the CLI."""
    app()


if __name__ == '__main__':  # pragma: no cover
    main()
