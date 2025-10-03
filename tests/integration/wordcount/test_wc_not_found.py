"""Integration test for node not found error handling."""

from pathlib import Path
from tempfile import TemporaryDirectory

from typer.testing import CliRunner

from prosemark.cli.main import app
from prosemark.domain.models import NodeId


def test_node_not_found() -> None:
    """Test that missing node returns error and exits with code 1."""
    with TemporaryDirectory() as tmpdir:
        project_path = Path(tmpdir)

        # Initialize prosemark project structure
        (project_path / '_binder.md').write_text('# Binder\n')

        # Use a valid UUID that doesn't exist
        non_existent_id = str(NodeId('0199a89e-ffff-7ce2-8b02-dcbbb7de3ae8'))

        runner = CliRunner(mix_stderr=False)
        result = runner.invoke(app, ['wc', non_existent_id, '--path', str(project_path)])

        # Should exit with error code 1
        assert result.exit_code == 1

        # Should output error message to stderr
        assert 'Error: Node not found' in result.stderr

        # Should still output '0' to stdout for scriptability
        assert result.stdout.strip() == '0'
