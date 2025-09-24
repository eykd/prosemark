"""Test append behavior for freewrite sessions with existing files."""

from pathlib import Path
from unittest.mock import patch

import pytest
from typer.testing import CliRunner

from prosemark.cli.main import app


class TestFreewriteAppendBehavior:
    """Test that freewrite sessions append to existing files instead of overwriting."""

    @pytest.fixture
    def runner(self) -> CliRunner:
        """Create a CLI runner for testing."""
        return CliRunner()

    @pytest.fixture
    def project(self, tmp_path: Path) -> Path:
        """Create a basic project."""
        project_dir = tmp_path / 'append_test_project'
        project_dir.mkdir()

        runner = CliRunner()
        runner.invoke(app, ['init', '--title', 'Append Test', '--path', str(project_dir)])

        return project_dir

    def test_freewrite_session_appends_to_existing_file(self, runner: CliRunner, project: Path) -> None:
        """Test that a new freewrite session appends to an existing file."""
        # Create an initial freewrite file with content
        existing_file = project / '2025-09-24-1800.md'
        existing_content = """---
type: "freewrite"
session_id: "original-session-id"
created: "2025-09-24T18:00:00.000000+00:00"
title: "Original Session"
---

# Freewrite Session

This is the original content.
More original content here.
"""
        existing_file.write_text(existing_content)

        with patch('prosemark.adapters.editor_launcher_system.subprocess.run') as mock_run:
            mock_run.return_value.returncode = 0
            with patch('prosemark.freewriting.adapters.freewrite_service_adapter.datetime') as mock_datetime:
                # Mock datetime to match the existing file's timestamp
                from datetime import UTC, datetime

                fixed_time = datetime(2025, 9, 24, 18, 0, 0, tzinfo=UTC)
                mock_datetime.now.return_value = fixed_time
                mock_datetime.side_effect = datetime

                # Start a new freewrite session that would create the same filename
                result = runner.invoke(app, ['write', '--title', 'New Session', '--path', str(project)])
                assert result.exit_code == 0

        # Read the file content after the session
        final_content = existing_file.read_text()

        # Verify original content is preserved
        assert 'This is the original content.' in final_content
        assert 'More original content here.' in final_content

        # Verify original session metadata is preserved
        assert 'Original Session' in final_content  # Original title should remain
        assert 'original-session-id' in final_content  # Original session ID should remain

    def test_freewrite_loads_existing_content_for_display(self, runner: CliRunner, project: Path) -> None:
        """Test that existing content is loaded and available for display in TUI."""
        # Create an existing freewrite file with content
        existing_file = project / '2025-09-24-1801.md'
        existing_content = """---
type: "freewrite"
session_id: "test-session-id"
created: "2025-09-24T18:01:00.000000+00:00"
title: "Test Session"
---

# Freewrite Session

Line 1 of existing content
Line 2 of existing content
Line 3 of existing content
"""
        existing_file.write_text(existing_content)

        with patch('prosemark.adapters.editor_launcher_system.subprocess.run') as mock_run:
            mock_run.return_value.returncode = 0
            with patch('prosemark.freewriting.adapters.freewrite_service_adapter.datetime') as mock_datetime:
                # Mock datetime to match the existing file's timestamp
                from datetime import UTC, datetime

                fixed_time = datetime(2025, 9, 24, 18, 1, 0, tzinfo=UTC)
                mock_datetime.now.return_value = fixed_time
                mock_datetime.side_effect = datetime

                # Start a freewrite session - this should load existing content
                result = runner.invoke(app, ['write', '--title', 'Another Session', '--path', str(project)])
                assert result.exit_code == 0

        # File should still contain original content (no overwrite)
        final_content = existing_file.read_text()
        assert 'Line 1 of existing content' in final_content
        assert 'Line 2 of existing content' in final_content
        assert 'Line 3 of existing content' in final_content
        # Original title should be preserved
        assert 'Test Session' in final_content
