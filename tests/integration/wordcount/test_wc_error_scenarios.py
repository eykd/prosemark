"""Integration tests for various error scenarios in wc command."""

from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

from typer.testing import CliRunner

from prosemark.adapters.binder_repo_fs import BinderRepoFs
from prosemark.cli.main import app
from prosemark.domain.models import BinderItem, NodeId


def test_wc_compilation_failed_for_all_roots() -> None:
    """Test error when compilation fails without specific node_id."""
    with TemporaryDirectory() as tmpdir:
        project_path = Path(tmpdir)

        # Initialize project but don't create binder file to cause compilation error
        # This will trigger CompileNodeNotFoundError during all-roots compilation

        runner = CliRunner(mix_stderr=False)
        # Mock to force a compilation error
        with patch('prosemark.cli.wc.CompileSubtreeUseCase') as mock_compile:
            from prosemark.ports.compile.service import NodeNotFoundError as CompileNodeNotFoundError

            mock_compile.return_value.compile_subtree.side_effect = CompileNodeNotFoundError(
                NodeId('0199a89e-e5f4-7ce2-8b02-dcbbb7de3ae8')
            )

            result = runner.invoke(app, ['wc', '--path', str(project_path)])

            # Should exit with error code 1
            assert result.exit_code == 1

            # Should output error message to stderr
            assert 'Error: Compilation failed' in result.stderr

            # Should still output '0' to stdout for scriptability
            assert result.stdout.strip() == '0'


def test_wc_generic_exception() -> None:
    """Test generic exception handling."""
    with TemporaryDirectory() as tmpdir:
        project_path = Path(tmpdir)

        # Initialize prosemark project structure
        (project_path / '_binder.md').write_text('# Binder\n')

        # Create a node
        node_id = NodeId('0199a89e-e5f4-7ce2-8b02-dcbbb7de3ae8')
        (project_path / f'{node_id}.md').write_text('---\ntitle: Test\n---\n\ntest')
        (project_path / f'{node_id}.notes.md').write_text(f'# [[{node_id}]]\n')

        binder_repo = BinderRepoFs(project_path)
        binder = binder_repo.load()
        binder.add_root_item(BinderItem(display_title='Test', node_id=node_id))
        binder_repo.save(binder)

        runner = CliRunner(mix_stderr=False)

        # Mock to force a generic exception
        with patch('prosemark.cli.wc.WordCountUseCase') as mock_usecase:
            mock_usecase.return_value.count_words.side_effect = RuntimeError('Unexpected error')

            result = runner.invoke(app, ['wc', str(node_id), '--path', str(project_path)])

            # Should exit with error code 1
            assert result.exit_code == 1

            # Should output error message to stderr
            assert 'Error: Word count failed' in result.stderr

            # Should still output '0' to stdout for scriptability
            assert result.stdout.strip() == '0'
