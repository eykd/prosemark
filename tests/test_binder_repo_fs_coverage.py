"""Coverage tests for binder_repo_fs missing lines."""

from pathlib import Path
from unittest.mock import patch

import pytest

from prosemark.adapters.binder_repo_fs import BinderRepoFs
from prosemark.exceptions import BinderFormatError, FileSystemError


class TestBinderRepoFsCoverage:
    """Test uncovered lines in BinderRepoFs."""

    def test_load_os_error_reading_file(self) -> None:
        """Test load method handles OSError when reading file (lines 75-77)."""
        project_root = Path('/test/project')
        repo = BinderRepoFs(project_root)

        # Mock Path.exists to return True and Path.read_text to raise OSError
        with (
            patch('pathlib.Path.exists', return_value=True),
            patch('pathlib.Path.read_text', side_effect=OSError('Permission denied')),
            pytest.raises(FileSystemError) as exc_info,
        ):
            repo.load()

        assert 'Cannot read binder file: Permission denied' in str(exc_info.value)

    def test_load_parse_error(self) -> None:
        """Test load method handles parsing errors (lines 89-91)."""
        project_root = Path('/test/project')
        repo = BinderRepoFs(project_root)

        # Mock the binder file to exist and return content
        mock_content = """
# Test Binder

<!-- BEGIN_MANAGED_BLOCK -->
- Invalid content that will cause parsing error
<!-- END_MANAGED_BLOCK -->
"""

        with (
            patch('pathlib.Path.exists', return_value=True),
            patch('pathlib.Path.read_text', return_value=mock_content),
            patch.object(repo.parser, 'parse_to_binder', side_effect=Exception('Parse error')),
            pytest.raises(BinderFormatError) as exc_info,
        ):
            # Mock the parser to raise an exception
            repo.load()

        assert 'Failed to parse binder content: Parse error' in str(exc_info.value)

    def test_update_content_no_managed_block(self) -> None:
        """Test _update_managed_block creates new content when no managed block exists (line 165)."""
        project_root = Path('/test/project')
        repo = BinderRepoFs(project_root)

        # Create content without managed block
        original_content = """
# Test Binder

Some existing content without managed block.
"""
        new_managed_content = '- [Chapter 1](chapter-1.md)'

        # Test the private method directly
        result = repo._update_managed_block(original_content, new_managed_content)

        # Should call _create_new_content since no managed block exists
        assert '<!-- BEGIN_MANAGED_BLOCK -->' in result
        assert '<!-- END_MANAGED_BLOCK -->' in result
        assert new_managed_content in result
        # _create_new_content generates new structure, may not preserve original content
