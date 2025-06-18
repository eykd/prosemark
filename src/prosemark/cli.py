"""The main Prosemark command line interface.

This module provides the command-line interface for the Prosemark application,
allowing users to manage projects and nodes through the terminal.
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import IO, TYPE_CHECKING, no_type_check

import click
import click_extra
import click_extra.colorize
from click_extra import Color, Style

from prosemark.adapters.cli import CLIResult, CLIService
from prosemark.adapters.session import SessionService
from prosemark.repositories.project import ProjectRepository

if TYPE_CHECKING:  # pragma: no cover
    from click.core import Context as ClickContext

    from prosemark.domain.nodes import NodeID

# Adjust the default theme to improve readability of the help text:
click_extra.colorize.default_theme = click_extra.colorize.default_theme.with_(
    # click-extra type annotations appear to be incorrect...
    default=Style(fg=Color.bright_green),  # type: ignore[arg-type]
    metavar=Style(fg=Color.bright_cyan),  # type: ignore[arg-type]
    bracket=Style(fg=Color.bright_white),  # type: ignore[arg-type]
)


@no_type_check
@click_extra.extra_group()
@click_extra.extra_version_option()
@click_extra.option(
    '--data-dir',
    default='.',
    help='Directory where project data is stored',
    type=click.Path(),
)
@click_extra.option(
    '--verbose',
    '-v',
    is_flag=True,
    default=False,
    help='Enable verbose output (print tracebacks on errors)',
)
@click_extra.option(
    '--pager/--no-pager',
    default=True,
    help='Use a pager to display long output',
)
@click.pass_context
def main(ctx: ClickContext, data_dir: str, verbose: bool, pager: bool) -> None:  # noqa: FBT001
    """Prosemark - A tool for structured document creation and management.

    Prosemark helps you organize your writing projects with a hierarchical
    structure of nodes, each containing content, notes, and metadata.
    """
    from prosemark.storages.filesystem import FilesystemMdNodeStorage

    ctx.ensure_object(dict)
    ctx.obj['data_dir'] = data_dir
    ctx.obj['verbose'] = verbose
    ctx.obj['pager'] = pager
    # Create storage and repository instances
    storage = FilesystemMdNodeStorage(Path(data_dir))
    repository = ProjectRepository(storage)
    ctx.obj['repository'] = repository
    ctx.obj['cli_service'] = CLIService(repository)
    ctx.obj['session_service'] = SessionService(repository)


@no_type_check
@main.command()
@click.argument('title')
@click_extra.option('--card', '-c', help='Brief summary of the project')
@click.pass_context
def init(ctx: ClickContext, title: str, card: str | None = None) -> None:
    """Create a new project.

    TITLE is the title of the new project to create.
    """
    cli_service = ctx.obj['cli_service']
    result = cli_service.init_project(title, card)
    _echo_result(ctx, result)


@no_type_check
@main.command()
@click.pass_context
def info(ctx: ClickContext) -> None:
    """Display information about the current project."""
    cli_service = ctx.obj['cli_service']
    _echo_result(ctx, cli_service.get_project_info())


@no_type_check
@main.command()
@click.argument('parent_id')
@click.argument('title')
@click_extra.option('--card', '-c', help='Brief summary of the node')
@click_extra.option('--text', '-t', help='Main content of the node')
@click_extra.option('--notes', '-n', help='Additional notes about the node')
@click_extra.option('--position', '-p', type=int, help='Position to insert the node')
@click.pass_context
def add(
    ctx: ClickContext,
    parent_id: str,
    title: str,
    card: str = '',
    text: str = '',
    notes: str = '',
    position: int | None = None,
) -> None:
    """Add a new node to the project.

    PARENT_ID is the ID of the parent node.
    TITLE is the title of the new node.
    """
    cli_service = ctx.obj['cli_service']
    result = cli_service.add_node(
        parent_id=parent_id,
        title=title,
        card=card,
        text=text,
        notes=notes,
        position=position,
    )
    _echo_result(ctx, result)


@no_type_check
@main.command()
@click.argument('node_id')
@click.pass_context
def remove(ctx: ClickContext, node_id: NodeID) -> None:
    """Remove a node from the project.

    NODE_ID is the ID of the node to remove.
    """
    cli_service = ctx.obj['cli_service']
    result = cli_service.remove_node(node_id)
    _echo_result(ctx, result)


@no_type_check
@main.command()
@click.argument('node_id')
@click.argument('new_parent_id')
@click_extra.option('--position', '-p', type=int, help='Position to insert the node')
@click.pass_context
def move(ctx: ClickContext, node_id: NodeID, new_parent_id: NodeID, position: int | None = None) -> None:
    """Move a node to a new parent.

    NODE_ID is the ID of the node to move.
    NEW_PARENT_ID is the ID of the new parent node.
    """
    cli_service = ctx.obj['cli_service']
    result = cli_service.move_node(node_id, new_parent_id, position)
    _echo_result(ctx, result)


@no_type_check
@main.command()
@click.argument('node_id')
@click.pass_context
def show(ctx: ClickContext, node_id: NodeID) -> None:
    """Display node content.

    NODE_ID is the ID of the node to display.
    """
    cli_service = ctx.obj['cli_service']
    result = cli_service.show_node(node_id)

    _echo_result(ctx, result)


@no_type_check
@main.command()
@click.argument('node_id')
@click_extra.option(
    '--input-file',
    'input_file',
    type=click.File('r'),
    default=None,
    help='Read content from file or stdin ("-" for stdin)',
)
@click_extra.option('--editor/--no-editor', default=True, help='Open in editor')
@click.pass_context
def edit(
    ctx: ClickContext,
    node_id: NodeID,
    input_file: IO[str] | None = None,
    editor: bool = True,  # noqa: FBT001, FBT002
) -> None:
    """Edit node content with the default text editor.

    NODE_ID is the ID of the node to edit.
    """
    cli_service = ctx.obj['cli_service']

    # Prepare the node content for editing
    result = cli_service.prepare_node_for_editor(node_id)
    if not result.success:  # pragma: no cover
        click.echo(result.message, err=True)
        return

    if input_file is not None:
        edited_content = input_file.read()
    elif editor:  # pragma: no cover
        # Open the editor with the formatted content
        tmp = click.edit(''.join(result.message), extension='.md')
        edited_content = tmp if tmp is not None else ''
    else:
        edited_content = ''.join(result.message)

    # Update the node with edited content
    _echo_result(ctx, cli_service.edit_node(node_id, edited_content))


@no_type_check
@main.command()
@click_extra.option('--node-id', '-n', help='ID of the node to start from (defaults to root)')
@click.pass_context
def structure(ctx: ClickContext, node_id: NodeID | None = None) -> None:
    """Display the project structure."""
    cli_service = ctx.obj['cli_service']

    _echo_result(ctx, cli_service.get_project_structure(node_id))


@no_type_check
@main.command(name='session')
@click.argument('node_id')
@click_extra.option('-w', '--words', type=int, help='Word count goal for this session')
@click_extra.option('-t', '--time', type=int, help='Session time limit in minutes')
@click_extra.option(
    '--timer',
    type=click.Choice(['none', 'visible', 'alert']),
    default='visible',
    help='Timer display mode (default: visible)',
)
@click_extra.option(
    '--stats',
    type=click.Choice(['none', 'minimal', 'detailed']),
    default='minimal',
    help='Stats display mode (default: minimal)',
)
@click_extra.option('--no-prompt', is_flag=True, help='Skip goal/time prompts when not specified')
@click.pass_context
def node_session(
    ctx: ClickContext,
    node_id: NodeID,
    *,
    words: int | None = None,
    time: int | None = None,
    timer: str = 'visible',
    stats: str = 'minimal',
    no_prompt: bool = False,
) -> None:
    """Start a focused writing session for a node.

    NODE_ID is the ID of the node to be edited.
    """
    repository = ctx.obj['repository']
    session_service = SessionService(repository)

    success, message = session_service.start_session(
        node_id=node_id,
        word_goal=words,
        time_limit=time,
        timer_mode=timer,
        stats_mode=stats,
        no_prompt=no_prompt,
    )

    if not success:  # pragma: no cover
        click.echo('\n'.join(message), err=True)
    else:  # pragma: no cover
        click.echo('\n'.join(message))


@no_type_check
@main.command()
@click_extra.option('-w', '--words', type=int, help='Word count goal for this session')
@click_extra.option('-t', '--time', type=int, help='Session time limit in minutes')
@click_extra.option(
    '--timer',
    type=click.Choice(['none', 'visible', 'alert']),
    default='visible',
    help='Timer display mode (default: visible)',
)
@click_extra.option(
    '--stats',
    type=click.Choice(['none', 'minimal', 'detailed']),
    default='minimal',
    help='Stats display mode (default: minimal)',
)
@click_extra.option('--no-prompt', is_flag=True, help='Skip goal/time prompts when not specified')
@click_extra.option('--date', help='Use specific date (YYYY-MM-DD) instead of today')
@click_extra.option('--suffix', default='daily', help="Custom suffix instead of 'daily' (e.g., 'morning', 'journal')")
@click.pass_context
def freewrite(
    ctx: ClickContext,
    *,
    words: int | None = None,
    time: int | None = None,
    timer: str = 'visible',
    stats: str = 'minimal',
    no_prompt: bool = False,
    date: str | None = None,
    suffix: str = 'daily',
) -> None:
    """Start a freewriting session for today's date.

    Creates or opens a file named YYYYMMDD0000 daily.md in the project root.
    This file is intentionally excluded from the binder structure to maintain
    separation between structured project work and free-form creative expression.
    """
    repository = ctx.obj['repository']
    session_service = SessionService(repository)

    success, message = session_service.start_freewrite_session(
        word_goal=words,
        time_limit=time,
        timer_mode=timer,
        stats_mode=stats,
        no_prompt=no_prompt,
        date_str=date,
        suffix=suffix,
    )

    if not success:
        click.echo('\n'.join(message), err=True)  # pragma: no cover
    else:
        click.echo('\n'.join(message))


@no_type_check
@main.group()
@click.pass_context
def card(ctx: ClickContext) -> None:
    """Manage cards associated with project nodes."""


@no_type_check
@card.command()
@click.argument('node_id')
@click_extra.option('-t', '--text', help='Initial text for the card')
@click_extra.option('--color', help='Color code for the card')
@click_extra.option('--status', help='Status label for the card')
@click.pass_context
def create(
    ctx: ClickContext, node_id: NodeID, text: str | None = None, color: str | None = None, status: str | None = None
) -> None:
    """Create a card for a node (if none exists).

    NODE_ID is the ID of the node to create a card for.
    """
    cli_service = ctx.obj['cli_service']
    result = cli_service.create_card(node_id, text, color, status)
    _echo_result(ctx, result)


@no_type_check
@card.command('edit')
@click.argument('node_id')
@click_extra.option(
    '--input-file',
    'input_file',
    type=click.File('r'),
    default=None,
    help='Read content from file or stdin ("-" for stdin)',
)
@click_extra.option('--editor', is_flag=True, help='Open in editor')
@click.pass_context
def edit_card(ctx: ClickContext, node_id: NodeID, input_file: IO[str] | None = None, *, editor: bool = False) -> None:
    """Edit a node's card in the default text editor.

    NODE_ID is the ID of the node whose card will be edited.
    """
    cli_service = ctx.obj['cli_service']

    if input_file is not None:
        edited_content = input_file.read()
        result = cli_service.edit_card(node_id, edited_content)
    elif editor:  # pragma: no cover
        # Prepare the card content for editing
        result = cli_service.prepare_card_for_editor(node_id)
        if not result.success:
            _echo_result(ctx, result)
            return

        # Open the editor with the formatted content
        tmp = click.edit(result.data)
        edited_content = tmp if tmp is not None else ''

        # Update the card with edited content if not aborted
        if edited_content is not None:
            result = cli_service.edit_card(node_id, edited_content)
        else:
            result = CLIResult(success=True, message=['Edit aborted, no changes made.'])
    else:
        # Interactive mode not implemented yet
        result = CLIResult(success=False, message=['Non-editor mode not implemented yet.'])

    _echo_result(ctx, result)


@no_type_check
@card.command('show')
@click.argument('node_id')
@click.pass_context
def show_card(ctx: ClickContext, node_id: NodeID) -> None:
    """Display a node's card content.

    NODE_ID is the ID of the node whose card will be displayed.
    """
    cli_service = ctx.obj['cli_service']
    result = cli_service.show_card(node_id)
    _echo_result(ctx, result)


@no_type_check
@card.command('remove')
@click.argument('node_id')
@click.pass_context
def remove_card(ctx: ClickContext, node_id: NodeID) -> None:
    """Remove a node's card.

    NODE_ID is the ID of the node whose card will be removed.
    """
    cli_service = ctx.obj['cli_service']
    result = cli_service.remove_card(node_id)
    _echo_result(ctx, result)


@no_type_check
@card.command('list')
@click_extra.option(
    '--output-format',
    'output_format',
    type=click.Choice(['text', 'json']),
    default='text',
    help='Output format (default: text)',
)
@click.pass_context
def list_cards(ctx: ClickContext, output_format: str = 'text') -> None:
    """List all nodes with cards."""
    cli_service = ctx.obj['cli_service']
    result = cli_service.list_cards(output_format)
    _echo_result(ctx, result)


@no_type_check
@card.command()
@click.argument('node_id')
@click_extra.option('-w', '--words', type=int, help='Word count goal for this session')
@click_extra.option('-t', '--time', type=int, help='Session time limit in minutes')
@click_extra.option(
    '--timer',
    type=click.Choice(['none', 'visible', 'alert']),
    default='visible',
    help='Timer display mode (default: visible)',
)
@click_extra.option(
    '--stats',
    type=click.Choice(['none', 'minimal', 'detailed']),
    default='minimal',
    help='Stats display mode (default: minimal)',
)
@click_extra.option('--no-prompt', is_flag=True, help='Skip goal/time prompts when not specified')
@click.pass_context
def session(
    ctx: ClickContext,
    node_id: NodeID,
    *,
    words: int | None = None,
    time: int | None = None,
    timer: str = 'visible',
    stats: str = 'minimal',
    no_prompt: bool = False,
) -> None:
    """Start a focused card writing session.

    NODE_ID is the ID of the node whose card will be edited.
    """
    repository = ctx.obj['repository']
    session_service = SessionService(repository)

    success, message = session_service.start_card_session(
        node_id=node_id,
        word_goal=words,
        time_limit=time,
        timer_mode=timer,
        stats_mode=stats,
        no_prompt=no_prompt,
    )

    if not success:
        click.echo('\n'.join(message), err=True)  # pragma: no cover


def _echo_result(ctx: ClickContext, result: CLIResult) -> None:
    if not result.success:  # pragma: no cover
        if isinstance(result.message, str):
            click.echo(result.message, err=True)
        else:
            for line in result.message:
                click.echo(line, nl=False, err=True)
        return

    if isinstance(result.message, str):  # pragma: no cover
        if ctx.obj['pager']:
            click.echo_via_pager(result.message)
        else:  # pragma: no cover
            click.echo(result.message)
    else:
        if ctx.obj['pager']:
            click.echo_via_pager(result.message)
        else:  # pragma: no cover
            for line in result.message:
                click.echo(line, nl=False)


if __name__ == '__main__':  # pragma: no cover
    try:
        main()
    except Exception as exc:  # noqa: BLE001  # TODO: Narrow exception handling for production
        import click

        click.echo(f'Error: {exc}', err=True)
        import sys

        sys.exit(1)
