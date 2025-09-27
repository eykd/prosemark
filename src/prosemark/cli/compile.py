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
    node_id: Annotated[str, typer.Argument(help='Node ID to compile')],
    path: Annotated[Path | None, typer.Option('--path', '-p', help='Project directory')] = None,
) -> None:
    """Compile a node and its subtree into concatenated plain text."""
    try:
        project_root = path or Path.cwd()

        # Validate the node ID format
        try:
            target_node_id = NodeId(node_id)
        except Exception as e:
            typer.echo(f'Error: Invalid node ID format: {node_id}', err=True)
            raise typer.Exit(1) from e

        # Wire up dependencies
        clock = ClockSystem()
        editor = EditorLauncherSystem()
        node_repo = NodeRepoFs(project_root, editor, clock)

        # Create use case
        compile_use_case = CompileSubtreeUseCase(node_repo)

        # Create request
        request = CompileRequest(node_id=target_node_id, include_empty=False)

        # Execute compilation
        result = compile_use_case.compile_subtree(request)

        # Output the compiled content to stdout
        typer.echo(result.content)

    except (NodeNotFoundError, CompileNodeNotFoundError) as e:
        typer.echo(f'Error: Node not found: {node_id}', err=True)
        raise typer.Exit(1) from e

    except Exception as e:
        typer.echo(f'Error: Compilation failed: {e}', err=True)
        raise typer.Exit(1) from e
