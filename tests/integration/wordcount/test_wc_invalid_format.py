"""Integration test for invalid node ID format error handling."""

from pathlib import Path
from tempfile import TemporaryDirectory

from typer.testing import CliRunner

from prosemark.cli.main import app


def test_invalid_node_id_format() -> None:
    """Test that invalid node ID format returns error and exits with code 1."""
    with TemporaryDirectory() as tmpdir:
        project_path = Path(tmpdir)

        # Initialize prosemark project structure
        (project_path / '_binder.md').write_text('# Binder\n')

        runner = CliRunner(mix_stderr=False)
        result = runner.invoke(app, ['wc', 'not-a-valid-uuid', '--path', str(project_path)])

        # Should exit with error code 1
        assert result.exit_code == 1

        # Should output error message to stderr
        assert 'Error: Invalid node ID format' in result.stderr

        # Should still output '0' to stdout for scriptability
        assert result.stdout.strip() == '0'
