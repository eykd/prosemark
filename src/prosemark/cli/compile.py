"""CLI command for compiling node subtrees."""

from pathlib import Path
from typing import Annotated

import typer

from prosemark.adapters.clock_system import ClockSystem
from prosemark.adapters.editor_launcher_system import EditorLauncherSystem
from prosemark.adapters.node_repo_fs import NodeRepoFs
from prosemark.app.compile.use_cases import CompileSubtreeUseCase
from prosemark.domain.compile.models import CompileRequest
from prosemark.domain.models import NodeId
from prosemark.exceptions import NodeNotFoundError
from prosemark.ports.compile.service import NodeNotFoundError as CompileNodeNotFoundError


def compile_command(
    node_id: Annotated[
        str | None,
        typer.Argument(help='Node ID to compile. Omit to compile all root nodes.'),
    ] = None,
    path: Annotated[Path | None, typer.Option('--path', '-p', help='Project directory')] = None,
    include_empty: Annotated[  # noqa: FBT002
        bool, typer.Option('--include-empty', help='Include nodes with empty content')
    ] = False,
) -> None:
    """Compile a node subtree or all root nodes into concatenated plain text.

    If NODE_ID is provided, compiles that specific node and its descendants.
    If NODE_ID is omitted, compiles all materialized root nodes in binder order.
    """
    try:
        project_root = path or Path.cwd()

        # Wire up dependencies
        clock = ClockSystem()
        editor = EditorLauncherSystem()
        node_repo = NodeRepoFs(project_root, editor, clock)

        # Import BinderRepoFs here to avoid circular imports
        from prosemark.adapters.binder_repo_fs import BinderRepoFs

        binder_repo = BinderRepoFs(project_root)

        # Create use case
        compile_use_case = CompileSubtreeUseCase(node_repo, binder_repo)

        # Handle optional node_id
        if node_id is None:
            # Compile all roots
            request = CompileRequest(node_id=None, include_empty=include_empty)
        else:
            # Validate and compile specific node
            try:
                target_node_id = NodeId(node_id)
            except Exception as e:
                typer.echo(f'Error: Invalid node ID format: {node_id}', err=True)
                raise typer.Exit(1) from e

            request = CompileRequest(node_id=target_node_id, include_empty=include_empty)

        # Execute compilation
        result = compile_use_case.compile_subtree(request)

        # Output the compiled content to stdout
        typer.echo(result.content)

    except (NodeNotFoundError, CompileNodeNotFoundError) as e:
        if node_id is not None:
            typer.echo(f'Error: Node not found: {node_id}', err=True)
        else:
            typer.echo(f'Error: Compilation failed: {e}', err=True)
        raise typer.Exit(1) from e

    except Exception as e:
        typer.echo(f'Error: Compilation failed: {e}', err=True)
        raise typer.Exit(1) from e
