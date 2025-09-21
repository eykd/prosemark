"""Tests for edge cases in domain entities to achieve 100% coverage."""

from pathlib import Path

import pytest

from prosemark.domain.entities import FreeformContent
from prosemark.exceptions import FreeformContentValidationError


class TestFreeformContentEdgeCases:
    """Test edge cases in FreeformContent for complete coverage."""

    def test_freeform_content_handles_invalid_timestamp_components(self) -> None:
        """Test FreeformContent raises error for invalid hour in timestamp."""
        # Arrange - filename with invalid hour (99)
        invalid_file_path = Path('20250231T9999_01932f3e-e7bc-7123-8abc-def012345678.md')

        # Act & Assert
        with pytest.raises(FreeformContentValidationError, match='Invalid hour in timestamp'):
            FreeformContent(
                id='01932f3e-e7bc-7123-8abc-def012345678',
                title='Test',
                created='2025-01-01T12:00:00Z',
                file_path=invalid_file_path,
            )

    def test_freeform_content_handles_invalid_created_timestamp_format(self) -> None:
        """Test FreeformContent raises error for invalid created timestamp format."""
        # Arrange - valid filename but invalid created timestamp
        valid_file_path = Path('20250101T1200_01932f3e-e7bc-7123-8abc-def012345678.md')
        invalid_created = 'not-a-valid-timestamp'

        # Act & Assert
        with pytest.raises(FreeformContentValidationError, match='Invalid created timestamp format'):
            FreeformContent(
                id='01932f3e-e7bc-7123-8abc-def012345678',
                title='Test',
                created=invalid_created,
                file_path=valid_file_path,
            )

    def test_freeform_content_handles_malformed_timestamp_in_filename(self) -> None:
        """Test FreeformContent raises error when timestamp format is wrong."""
        # Arrange - filename with malformed timestamp part (letters instead of numbers)
        malformed_file_path = Path('abcdEFGHijkl_01932f3e-e7bc-7123-8abc-def012345678.md')

        # Act & Assert
        with pytest.raises(FreeformContentValidationError, match='Invalid timestamp format in filename'):
            FreeformContent(
                id='01932f3e-e7bc-7123-8abc-def012345678',
                title='Test',
                created='2025-01-01T12:00:00Z',
                file_path=malformed_file_path,
            )

    def test_freeform_content_handles_partial_timestamp_in_filename(self) -> None:
        """Test FreeformContent raises error when timestamp is incomplete."""
        # Arrange - filename with incomplete timestamp (missing parts)
        incomplete_file_path = Path('202501_01932f3e-e7bc-7123-8abc-def012345678.md')

        # Act & Assert
        with pytest.raises(FreeformContentValidationError, match='Invalid timestamp format in filename'):
            FreeformContent(
                id='01932f3e-e7bc-7123-8abc-def012345678',
                title='Test',
                created='2025-01-01T12:00:00Z',
                file_path=incomplete_file_path,
            )

    def test_freeform_content_handles_non_iso_created_timestamp(self) -> None:
        """Test FreeformContent raises error for created timestamp in wrong format."""
        # Arrange - valid filename but created timestamp not in ISO format
        valid_file_path = Path('20250101T1200_01932f3e-e7bc-7123-8abc-def012345678.md')
        non_iso_created = '2025/01/01 12:00:00'  # Wrong format

        # Act & Assert
        with pytest.raises(FreeformContentValidationError, match='Invalid created timestamp format'):
            FreeformContent(
                id='01932f3e-e7bc-7123-8abc-def012345678',
                title='Test',
                created=non_iso_created,
                file_path=valid_file_path,
            )

    def test_freeform_content_handles_non_numeric_timestamp_components(self) -> None:
        """Test FreeformContent raises ValueError for non-numeric timestamp components."""
        # Arrange - filename with valid format but non-numeric characters in positions
        # that would cause int() conversion to fail
        file_path = Path('202a01b1T12c0_01932f3e-e7bc-7123-8abc-def012345678.md')

        # Act & Assert
        with pytest.raises(FreeformContentValidationError, match='Invalid timestamp components in filename'):
            FreeformContent(
                id='01932f3e-e7bc-7123-8abc-def012345678',
                title='Test',
                created='2025-01-01T12:00:00Z',
                file_path=file_path,
            )
