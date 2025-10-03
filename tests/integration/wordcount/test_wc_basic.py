"""Integration test for basic word count (Quickstart Scenario 1)."""

from collections.abc import Iterator
from pathlib import Path
from tempfile import TemporaryDirectory

import pytest
from typer.testing import CliRunner

from prosemark.cli.main import app


@pytest.fixture
def test_project() -> Iterator[Path]:
    """Create a temporary test project."""
    with TemporaryDirectory() as tmpdir:
        project_path = Path(tmpdir)

        # Initialize prosemark project structure - create empty binder
        (project_path / '_binder.md').write_text('# Binder\n')

        yield project_path


def test_basic_word_count_single_node(test_project: Path) -> None:
    """Test word count for a single node with 'Hello world'."""
    from prosemark.adapters.binder_repo_fs import BinderRepoFs
    from prosemark.domain.models import BinderItem, NodeId

    # Create a test node with "Hello world" (2 words)
    node_id = NodeId('0199a89e-e5f4-7ce2-8b02-dcbbb7de3ae8')

    # Create node files manually
    draft_file = test_project / f'{node_id}.md'
    draft_file.write_text('---\ntitle: Test Node\n---\n\nHello world')

    notes_file = test_project / f'{node_id}.notes.md'
    notes_file.write_text(f'# [[{node_id}]]\n')

    # Add to binder
    binder_repo = BinderRepoFs(test_project)
    binder = binder_repo.load()
    item = BinderItem(display_title='Test Node', node_id=node_id)
    binder.add_root_item(item)
    binder_repo.save(binder)

    # Run wc command
    runner = CliRunner()
    result = runner.invoke(app, ['wc', str(node_id), '--path', str(test_project)])

    # Verify output
    assert result.exit_code == 0, f'Command failed: {result.output}'
    assert result.output.strip() == '2', f'Expected "2", got "{result.output.strip()}"'


def test_basic_word_count_no_stderr_on_success(test_project: Path) -> None:
    """Test that successful word count has no stderr output."""
    from prosemark.adapters.binder_repo_fs import BinderRepoFs
    from prosemark.domain.models import BinderItem, NodeId

    node_id = NodeId('0199a89e-e5f4-7ce2-8b02-dcbbb7de3ae9')

    # Create node files manually
    draft_file = test_project / f'{node_id}.md'
    draft_file.write_text('---\ntitle: Test\n---\n\ntest')

    notes_file = test_project / f'{node_id}.notes.md'
    notes_file.write_text(f'# [[{node_id}]]\n')

    binder_repo = BinderRepoFs(test_project)
    binder = binder_repo.load()
    item = BinderItem(display_title='Test', node_id=node_id)
    binder.add_root_item(item)
    binder_repo.save(binder)

    runner = CliRunner(mix_stderr=False)
    result = runner.invoke(app, ['wc', str(node_id), '--path', str(test_project)])

    assert result.exit_code == 0
    # No stderr output on success
    assert not result.stderr or result.stderr == ''
