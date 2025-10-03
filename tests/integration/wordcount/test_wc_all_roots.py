"""Integration test for counting all root nodes."""

from pathlib import Path
from tempfile import TemporaryDirectory

from typer.testing import CliRunner

from prosemark.adapters.binder_repo_fs import BinderRepoFs
from prosemark.cli.main import app
from prosemark.domain.models import BinderItem, NodeId


def test_count_all_roots_without_node_id() -> None:
    """Test word count for all root nodes when no node_id is provided."""
    with TemporaryDirectory() as tmpdir:
        project_path = Path(tmpdir)

        # Initialize prosemark project structure
        (project_path / '_binder.md').write_text('# Binder\n')

        # Create two root nodes
        node_id_1 = NodeId('0199a89e-e5f4-7ce2-8b02-dcbbb7de3ae1')
        node_id_2 = NodeId('0199a89e-e5f4-7ce2-8b02-dcbbb7de3ae2')

        # Create first node with "Hello world" (2 words)
        (project_path / f'{node_id_1}.md').write_text('---\ntitle: Node 1\n---\n\nHello world')
        (project_path / f'{node_id_1}.notes.md').write_text(f'# [[{node_id_1}]]\n')

        # Create second node with "Test content" (2 words)
        (project_path / f'{node_id_2}.md').write_text('---\ntitle: Node 2\n---\n\nTest content')
        (project_path / f'{node_id_2}.notes.md').write_text(f'# [[{node_id_2}]]\n')

        # Add both to binder as roots
        binder_repo = BinderRepoFs(project_path)
        binder = binder_repo.load()
        binder.add_root_item(BinderItem(display_title='Node 1', node_id=node_id_1))
        binder.add_root_item(BinderItem(display_title='Node 2', node_id=node_id_2))
        binder_repo.save(binder)

        # Run wc command without node_id
        runner = CliRunner()
        result = runner.invoke(app, ['wc', '--path', str(project_path)])

        # Should count all roots: 2 + 2 = 4 words
        assert result.exit_code == 0, f'Command failed: {result.output}'
        assert result.output.strip() == '4', f'Expected "4", got "{result.output.strip()}"'
