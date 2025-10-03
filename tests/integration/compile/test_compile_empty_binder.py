"""Integration test for empty binder handling during compilation."""

from pathlib import Path

import pytest
from typer.testing import CliRunner

from prosemark.cli.main import app


class TestCompileEmptyBinder:
    """Test compile command behavior with empty or placeholder-only binders."""

    @pytest.fixture
    def runner(self) -> CliRunner:
        """Create a CLI runner for testing."""
        return CliRunner()

    @pytest.fixture
    def project_dir(self, tmp_path: Path) -> Path:
        """Create a temporary project directory."""
        return tmp_path / 'test_project'

    def test_compile_empty_binder_silent_success(self, runner: CliRunner, project_dir: Path) -> None:
        """Empty binder produces empty output with exit code 0."""
        # Setup: Create binder with no roots
        project_dir.mkdir()
        result = runner.invoke(app, ['init', '--title', 'Empty Project', '--path', str(project_dir)])
        assert result.exit_code == 0

        # Don't add any nodes - binder is empty

        # Execute: Compile without node_id
        result = runner.invoke(app, ['compile', '--path', str(project_dir)])

        # Verify: Empty output, exit 0, no error
        assert result.exit_code == 0
        assert result.output.strip() == ''

    def test_compile_all_placeholder_roots(self, runner: CliRunner, project_dir: Path) -> None:
        """All-placeholder binder produces empty output with exit code 0."""
        # Setup: Initialize project
        project_dir.mkdir()
        result = runner.invoke(app, ['init', '--title', 'Test Project', '--path', str(project_dir)])
        assert result.exit_code == 0

        # Add placeholders only (no materialized nodes)
        # Manually edit binder to add placeholders
        binder_path = project_dir / '_binder.md'
        content = binder_path.read_text()

        # Add placeholders in the managed section
        content = content.replace(
            '<!-- END_MANAGED_BLOCK -->',
            '- [Placeholder 1]()\n- [Placeholder 2]()\n<!-- END_MANAGED_BLOCK -->',
        )
        binder_path.write_text(content)

        # Execute: Compile without node_id
        result = runner.invoke(app, ['compile', '--path', str(project_dir)])

        # Verify: Empty output, exit 0 (placeholders have no content)
        assert result.exit_code == 0
        assert result.output.strip() == ''

    def test_compile_empty_project_with_include_empty(self, runner: CliRunner, project_dir: Path) -> None:
        """Empty binder with --include-empty flag also produces empty output."""
        # Setup: Empty project
        project_dir.mkdir()
        result = runner.invoke(app, ['init', '--title', 'Empty Project', '--path', str(project_dir)])
        assert result.exit_code == 0

        # Execute: Compile with --include-empty flag
        result = runner.invoke(app, ['compile', '--include-empty', '--path', str(project_dir)])

        # Verify: Still empty output, exit 0
        assert result.exit_code == 0
        assert result.output.strip() == ''
