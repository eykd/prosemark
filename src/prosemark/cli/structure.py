"""CLI command for displaying project structure."""

import json
from pathlib import Path
from typing import TYPE_CHECKING, Any, Union

import click

from prosemark.adapters.binder_repo_fs import BinderRepoFs
from prosemark.adapters.logger_stdout import LoggerStdout
from prosemark.app.use_cases import ShowStructure
from prosemark.domain.binder import Item
from prosemark.exceptions import FileSystemError

if TYPE_CHECKING:
    from prosemark.domain.models import BinderItem


@click.command()
@click.option('--format', '-f', default='tree', type=click.Choice(['tree', 'json']), help='Output format')
def structure_command(format: str) -> None:
    """Display project hierarchy."""
    try:
        project_root = Path.cwd()

        # Wire up dependencies
        binder_repo = BinderRepoFs(project_root)
        logger = LoggerStdout()

        # Execute use case
        interactor = ShowStructure(
            binder_repo=binder_repo,
            logger=logger,
        )

        structure_str = interactor.execute()

        if format == 'tree':
            click.echo('Project Structure:')
            click.echo(structure_str)
        elif format == 'json':
            # For JSON format, we need to convert the tree to JSON
            binder = binder_repo.load()

            def item_to_dict(item: Union[Item, 'BinderItem']) -> dict[str, Any]:
                result: dict[str, Any] = {
                    'display_title': item.display_title if hasattr(item, 'display_title') else item.display_title,
                }
                node_id = item.id if hasattr(item, 'id') else (item.node_id if hasattr(item, 'node_id') else None)
                if node_id:
                    result['node_id'] = str(node_id)
                item_children = item.children if hasattr(item, 'children') else []
                if item_children:
                    result['children'] = [item_to_dict(child) for child in item_children]
                return result

            data: dict[str, list[dict[str, Any]]] = {'roots': [item_to_dict(item) for item in binder.roots]}
            click.echo(json.dumps(data, indent=2))

    except FileSystemError as e:
        click.echo(f'Error: {e}', err=True)
        raise SystemExit(1)
