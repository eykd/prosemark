"""CLI command for counting words in node subtrees."""

from pathlib import Path
from typing import Annotated

import typer

from prosemark.adapters.clock_system import ClockSystem
from prosemark.adapters.editor_launcher_system import EditorLauncherSystem
from prosemark.adapters.node_repo_fs import NodeRepoFs
from prosemark.adapters.wordcount.counter_standard import StandardWordCounter
from prosemark.app.compile.use_cases import CompileSubtreeUseCase
from prosemark.app.wordcount.use_cases import WordCountUseCase
from prosemark.domain.models import NodeId
from prosemark.domain.wordcount.models import WordCountRequest
from prosemark.domain.wordcount.service import WordCountService
from prosemark.exceptions import NodeIdentityError, NodeNotFoundError
from prosemark.ports.compile.service import NodeNotFoundError as CompileNodeNotFoundError


def wc_command(
    node_id: Annotated[
        str | None,
        typer.Argument(help='Node ID to count words in. Omit to count all root nodes.'),
    ] = None,
    path: Annotated[Path | None, typer.Option('--path', '-p', help='Project directory')] = None,
    include_empty: Annotated[  # noqa: FBT002
        bool, typer.Option('--include-empty', help='Include nodes with empty content')
    ] = False,
) -> None:
    """Count words in a node subtree or all root nodes.

    If NODE_ID is provided, counts words in that specific node and its descendants.
    If NODE_ID is omitted, counts words in all materialized root nodes in binder order.

    Output is a plain number to stdout, suitable for scripting:
        pmk wc <node-id>           # Count specific subtree
        pmk wc                     # Count all roots
        COUNT=$(pmk wc <node-id>)  # Capture in shell variable
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

        # Create compile use case
        compile_use_case = CompileSubtreeUseCase(node_repo, binder_repo)

        # Create word count components
        word_counter = StandardWordCounter()
        word_count_service = WordCountService(counter=word_counter)
        word_count_use_case = WordCountUseCase(compile_use_case=compile_use_case, word_count_service=word_count_service)

        # Handle optional node_id
        if node_id is None:
            # Count all roots
            request = WordCountRequest(node_id=None, include_empty=include_empty)
        else:
            # Validate and count specific node
            try:
                target_node_id = NodeId(node_id)
            except NodeIdentityError:
                typer.echo('0')  # Output 0 to stdout for scriptability
                typer.echo(f'Error: Invalid node ID format: {node_id}', err=True)
                raise typer.Exit(1) from None

            request = WordCountRequest(node_id=target_node_id, include_empty=include_empty)

        # Execute word count
        result = word_count_use_case.count_words(request)

        # Output the count to stdout (plain number, no labels)
        typer.echo(result.count)

    except typer.Exit:
        # Re-raise typer.Exit without modification
        raise

    except (NodeNotFoundError, CompileNodeNotFoundError):
        typer.echo('0')  # Output 0 to stdout for scriptability
        if node_id is not None:
            typer.echo(f'Error: Node not found: {node_id}', err=True)
        else:
            typer.echo('Error: Compilation failed', err=True)
        raise typer.Exit(1) from None

    except (OSError, RuntimeError) as e:
        # Catch specific expected exceptions
        typer.echo('0')  # Output 0 to stdout for scriptability
        typer.echo(f'Error: Word count failed: {e}', err=True)
        raise typer.Exit(1) from None
