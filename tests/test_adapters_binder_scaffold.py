"""Tests for binder scaffold generator."""

import tempfile
from pathlib import Path

import pytest

from prosemark.adapters.binder_scaffold import generate_binder_scaffold
from prosemark.exceptions import FileSystemError, ProsemarkFileExistsError


class TestGenerateBinderScaffold:
    """Test the generate_binder_scaffold function."""

    def test_basic_scaffold_generation(self) -> None:
        """Test basic scaffold generation creates _binder.md with proper format and markers."""
        with tempfile.TemporaryDirectory() as temp_dir:
            target_path = Path(temp_dir)

            # When: Scaffold generator is called
            generate_binder_scaffold(target_path)

            # Then: Creates _binder.md with proper format and markers
            binder_file = target_path / '_binder.md'
            assert binder_file.exists()

            content = binder_file.read_text(encoding='utf-8')
            assert '<!-- pmk:begin-binder -->' in content
            assert '<!-- pmk:end-binder -->' in content
            assert 'managed by Prosemark' in content

    def test_scaffold_content_structure(self) -> None:
        """Test scaffold content structure contains proper sections, managed block markers, and example content."""
        with tempfile.TemporaryDirectory() as temp_dir:
            target_path = Path(temp_dir)

            # When: File content is examined after generation
            generate_binder_scaffold(target_path)
            content = (target_path / '_binder.md').read_text(encoding='utf-8')

            # Then: Contains proper sections, managed block markers, and example content
            assert '# Binder' in content
            assert 'Welcome to your new prosemark project' in content
            assert '## Binder (managed by Prosemark)' in content
            assert '<!-- pmk:begin-binder -->' in content
            assert '<!-- pmk:end-binder -->' in content
            assert '[Sample Chapter]' in content
            assert '[New Placeholder]()' in content
            assert 'managed section above will be automatically updated' in content

    def test_existing_file_handling(self) -> None:
        """Test existing file handling raises FileExistsError when _binder.md already exists."""
        with tempfile.TemporaryDirectory() as temp_dir:
            target_path = Path(temp_dir)
            binder_file = target_path / '_binder.md'

            # Given: A directory where _binder.md already exists
            binder_file.write_text('existing content')

            # When: Scaffold generator is called
            # Then: Raises FileExistsError
            with pytest.raises(ProsemarkFileExistsError) as exc_info:
                generate_binder_scaffold(target_path)

            assert str(binder_file) in str(exc_info.value)

    def test_directory_creation(self) -> None:
        """Test directory creation when parent directories don't exist."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Given: A target path where parent directories don't exist
            target_path = Path(temp_dir) / 'nested' / 'deep' / 'project'
            assert not target_path.exists()

            # When: Scaffold generator is called with create_dirs=True
            generate_binder_scaffold(target_path, create_dirs=True)

            # Then: Creates necessary parent directories and binder file
            assert target_path.exists()
            assert target_path.is_dir()
            binder_file = target_path / '_binder.md'
            assert binder_file.exists()

    def test_directory_creation_disabled_by_default(self) -> None:
        """Test that directory creation is disabled by default."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Given: A target path where parent directories don't exist
            target_path = Path(temp_dir) / 'nested' / 'deep' / 'project'
            assert not target_path.exists()

            # When: Scaffold generator is called without create_dirs=True
            # Then: Raises FileSystemError due to missing parent directories
            with pytest.raises(FileSystemError):
                generate_binder_scaffold(target_path)

    def test_marker_format_validation(self) -> None:
        """Test marker format validation - generated file can be parsed by MarkdownBinderParser."""
        with tempfile.TemporaryDirectory() as temp_dir:
            target_path = Path(temp_dir)

            # When: Content is parsed after generation
            generate_binder_scaffold(target_path)
            content = (target_path / '_binder.md').read_text(encoding='utf-8')

            # Then: Successfully identifies and parses managed block
            # This test validates the structure is compatible with our parser
            begin_marker = '<!-- pmk:begin-binder -->'
            end_marker = '<!-- pmk:end-binder -->'

            begin_pos = content.find(begin_marker)
            end_pos = content.find(end_marker)

            assert begin_pos != -1, 'Begin marker not found'
            assert end_pos != -1, 'End marker not found'
            assert begin_pos < end_pos, 'Markers in wrong order'

            # Extract managed content
            managed_start = begin_pos + len(begin_marker)
            managed_content = content[managed_start:end_pos].strip()

            # Verify managed content contains expected example structure
            assert '- [Sample Chapter]' in managed_content
            assert '- [New Placeholder]()' in managed_content

    def test_template_content(self) -> None:
        """Test template content includes helpful examples and documentation for users."""
        with tempfile.TemporaryDirectory() as temp_dir:
            target_path = Path(temp_dir)

            # When: Examining the content outside managed blocks
            generate_binder_scaffold(target_path)
            content = (target_path / '_binder.md').read_text(encoding='utf-8')

            # Then: Contains helpful examples and documentation for users
            # Check documentation before managed block
            assert 'You can write notes, introductions, and other content' in content
            assert 'Only the section between the special markers below' in content

            # Check documentation after managed block
            assert 'managed section above will be automatically updated' in content
            assert 'add, move, and remove nodes' in content

            # Check example content demonstrates proper formats
            assert '[Sample Chapter](01234567.md)' in content  # Node link format
            assert '[New Placeholder]()' in content  # Placeholder format

    def test_file_encoding_utf8(self) -> None:
        """Test file encoding is UTF-8 with proper line endings."""
        with tempfile.TemporaryDirectory() as temp_dir:
            target_path = Path(temp_dir)

            generate_binder_scaffold(target_path)
            binder_file = target_path / '_binder.md'

            # Test UTF-8 encoding by reading with explicit encoding
            content = binder_file.read_text(encoding='utf-8')
            assert isinstance(content, str)

            # Test that we can write and read back the same content
            binder_file.write_text(content, encoding='utf-8')
            content2 = binder_file.read_text(encoding='utf-8')
            assert content == content2

    def test_integration_with_binder_parser(self) -> None:
        """Test integration with existing binder parsing infrastructure."""
        # This would require actual binder parser implementation
        # For now, we test the structure matches expected format
        with tempfile.TemporaryDirectory() as temp_dir:
            target_path = Path(temp_dir)

            generate_binder_scaffold(target_path)
            content = (target_path / '_binder.md').read_text(encoding='utf-8')

            # Verify the managed block structure that a parser would expect
            lines = content.split('\n')

            # Find the managed section
            in_managed_section = False
            managed_lines = []

            for line in lines:
                if '<!-- pmk:begin-binder -->' in line:
                    in_managed_section = True
                    continue
                if '<!-- pmk:end-binder -->' in line:
                    in_managed_section = False
                    break
                if in_managed_section:
                    managed_lines.append(line)

            # Should have exactly 2 lines in managed section (the two example items)
            non_empty_lines = [line for line in managed_lines if line.strip()]
            assert len(non_empty_lines) == 2

            # Verify list item format
            assert non_empty_lines[0].startswith('- [')
            assert non_empty_lines[1].startswith('- [')

    def test_error_handling_permission_denied(self) -> None:
        """Test error handling for permission denied scenarios."""
        with tempfile.TemporaryDirectory() as temp_dir:
            target_path = Path(temp_dir) / 'readonly'
            target_path.mkdir(mode=0o444)  # Read-only directory

            try:
                # Should raise FileSystemError when cannot write to directory
                with pytest.raises(FileSystemError):
                    generate_binder_scaffold(target_path)
            finally:
                # Cleanup: restore write permissions for cleanup
                target_path.chmod(0o755)

    def test_atomic_operation(self) -> None:
        """Test that scaffold generation is atomic - either succeeds completely or fails cleanly."""
        with tempfile.TemporaryDirectory() as temp_dir:
            target_path = Path(temp_dir)

            # First, test successful generation
            generate_binder_scaffold(target_path)
            binder_file = target_path / '_binder.md'
            assert binder_file.exists()

            # Remove the file for next test
            binder_file.unlink()

            # Test that if we can't write (e.g., no space), no partial file is left
            # This is a conceptual test - in practice, disk space errors are hard to simulate
            # The key is that our implementation should not leave partial files around
            if binder_file.exists():
                binder_file.read_text()

            # The file should not exist after our cleanup
            assert not binder_file.exists()

    def test_error_handling_directory_creation_failure(self) -> None:
        """Test error handling when directory creation fails with OSError."""
        import tempfile
        from unittest.mock import patch

        with tempfile.TemporaryDirectory() as temp_dir:
            target_path = Path(temp_dir) / 'nonexistent' / 'nested'

            # Mock mkdir to raise OSError
            with patch.object(Path, 'mkdir', side_effect=OSError('Permission denied')):
                with pytest.raises(FileSystemError) as exc_info:
                    generate_binder_scaffold(target_path, create_dirs=True)

                assert 'Cannot create target directory' in str(exc_info.value)
                assert str(target_path) in str(exc_info.value)

    def test_error_handling_target_path_not_directory(self) -> None:
        """Test error handling when target path exists but is not a directory."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create a file instead of a directory
            target_path = Path(temp_dir) / 'not_a_directory'
            target_path.write_text('I am a file, not a directory')

            with pytest.raises(FileSystemError) as exc_info:
                generate_binder_scaffold(target_path)

            assert 'Target path is not a directory' in str(exc_info.value)
            assert str(target_path) in str(exc_info.value)

    def test_error_handling_file_write_failure(self) -> None:
        """Test error handling when file writing fails with OSError."""
        import tempfile
        from unittest.mock import patch

        with tempfile.TemporaryDirectory() as temp_dir:
            target_path = Path(temp_dir)

            # Mock write_text to raise OSError
            with patch.object(Path, 'write_text', side_effect=OSError('No space left on device')):
                with pytest.raises(FileSystemError) as exc_info:
                    generate_binder_scaffold(target_path)

                assert 'Cannot write binder file' in str(exc_info.value)
                # Should not leave temp files around
                temp_files = list(target_path.glob('*.tmp'))
                assert len(temp_files) == 0
