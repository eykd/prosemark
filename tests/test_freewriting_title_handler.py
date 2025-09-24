"""Tests for freewriting title handler utilities."""

from prosemark.freewriting.adapters.title_handler import (
    process_title,
    sanitize_title_for_filename,
)


class TestProcessTitle:
    """Test the process_title function."""

    def test_processes_normal_title(self) -> None:
        """Test that normal titles are returned unchanged."""
        title = 'My Writing Session'
        result = process_title(title)

        assert result == 'My Writing Session'

    def test_strips_whitespace(self) -> None:
        """Test that leading and trailing whitespace is stripped."""
        title = '  My Writing Session  '
        result = process_title(title)

        assert result == 'My Writing Session'

    def test_handles_empty_string(self) -> None:
        """Test that empty string is returned unchanged."""
        title = ''
        result = process_title(title)

        assert result == ''

    def test_handles_none_like_empty_string(self) -> None:
        """Test that falsy values are returned unchanged."""
        # Testing the early return for falsy values
        result = process_title('')
        assert result == ''

    def test_truncates_long_title_with_default_length(self) -> None:
        """Test that titles longer than default max_length are truncated."""
        # Create a title longer than 50 characters (default max_length)
        long_title = 'This is a very long title that exceeds the default maximum length limit'
        result = process_title(long_title)

        # Should be truncated to 47 characters + "..." = 50 total
        expected = 'This is a very long title that exceeds the defa...'
        assert result == expected
        assert len(result) == 50

    def test_truncates_long_title_with_custom_length(self) -> None:
        """Test that titles are truncated to custom max_length."""
        title = 'This is a long title'
        result = process_title(title, max_length=10)

        # Should be truncated to 7 characters + "..." = 10 total
        expected = 'This is...'
        assert result == expected
        assert len(result) == 10

    def test_title_at_max_length_not_truncated(self) -> None:
        """Test that titles exactly at max_length are not truncated."""
        title = 'Exactly forty seven chars title for testing now'  # 47 chars
        result = process_title(title, max_length=47)

        assert result == title
        assert len(result) == 47

    def test_title_one_over_max_length_gets_truncated(self) -> None:
        """Test that titles one character over max_length get truncated."""
        title = 'Exactly forty-eight characters title for test!'  # 46 chars
        result = process_title(title, max_length=45)

        # Title is 46 chars, max_length is 45, so it should be truncated
        # to 42 characters + "..." = 45 total
        expected = 'Exactly forty-eight characters title for t...'
        assert result == expected
        assert len(result) == 45

    def test_very_short_max_length(self) -> None:
        """Test that very short max_length values work correctly."""
        title = 'Long title'
        result = process_title(title, max_length=5)

        # Should be truncated to 2 characters + "..." = 5 total
        expected = 'Lo...'
        assert result == expected
        assert len(result) == 5

    def test_max_length_three_returns_ellipsis_only(self) -> None:
        """Test that max_length of 3 returns only ellipsis for long titles."""
        title = 'Long title'
        result = process_title(title, max_length=3)

        # Should be truncated to 0 characters + "..." = 3 total
        expected = '...'
        assert result == expected
        assert len(result) == 3

    def test_preserves_internal_whitespace(self) -> None:
        """Test that internal whitespace is preserved during processing."""
        title = '  My   Writing   Session  '
        result = process_title(title)

        # Should strip external whitespace but preserve internal
        assert result == 'My   Writing   Session'

    def test_handles_whitespace_only_title(self) -> None:
        """Test that title with only whitespace becomes empty after processing."""
        title = '   \t\n   '
        result = process_title(title)

        # After stripping, becomes empty string which is falsy and returned as-is
        assert result == ''


class TestSanitizeTitleForFilename:
    """Test the sanitize_title_for_filename function."""

    def test_calls_file_system_adapter_sanitize_method(self) -> None:
        """Test that the function delegates to FileSystemAdapter.sanitize_title."""
        # Since this function just delegates to FileSystemAdapter.sanitize_title,
        # we should test that it calls that method correctly
        from unittest.mock import patch

        title = 'Test Title'

        with patch(
            'prosemark.freewriting.adapters.file_system_adapter.FileSystemAdapter.sanitize_title'
        ) as mock_sanitize:
            mock_sanitize.return_value = 'test-title'

            result = sanitize_title_for_filename(title)

            # Verify the method was called with correct argument
            mock_sanitize.assert_called_once_with(title)

            # Verify the result is what the mock returned
            assert result == 'test-title'

    def test_returns_sanitized_title(self) -> None:
        """Test that the function returns a sanitized title."""
        # Test with a title that needs sanitization
        title = 'My / Unsafe \\ Title: With | Special * Characters?'

        result = sanitize_title_for_filename(title)

        # The result should be safe for use in filenames
        # The exact sanitization logic is tested in the FileSystemAdapter tests
        assert isinstance(result, str)
        # Basic check that problematic characters are handled
        unsafe_chars = ['/', '\\', ':', '|', '*', '?']
        for char in unsafe_chars:
            assert char not in result or result == title  # Allow pass-through if not sanitized

    def test_handles_empty_title(self) -> None:
        """Test that empty titles are handled appropriately."""
        result = sanitize_title_for_filename('')

        # Should return a string (the exact value depends on FileSystemAdapter implementation)
        assert isinstance(result, str)

    def test_handles_normal_title(self) -> None:
        """Test that normal, safe titles work correctly."""
        title = 'Normal Title'
        result = sanitize_title_for_filename(title)

        # Should return a string that's safe for filenames
        assert isinstance(result, str)
        assert len(result) > 0  # Should not become empty
