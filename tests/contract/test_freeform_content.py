"""Contract tests for FreeformContent entity.

These tests define the behavioral contracts that any FreeformContent implementation must satisfy.
They will fail until the FreeformContent class is properly implemented.
"""

import re
from datetime import datetime
from pathlib import Path

import pytest

# These imports will fail until classes are implemented
from prosemark.domain.entities import FreeformContent
from prosemark.exceptions import FreeformContentValidationError


class TestFreeformContentContract:
    """Contract tests for FreeformContent entity."""

    def test_freeform_content_initialization_minimal(self) -> None:
        """Contract: FreeformContent can be created with minimal required fields."""
        uuid7_id = '0192f0c1-2345-7123-8abc-def012345678'
        created_time = datetime.fromisoformat('2025-09-20T15:30:00+00:00')
        file_path = Path('20250920T1530_0192f0c1-2345-7123-8abc-def012345678.md')

        content = FreeformContent(id=uuid7_id, title=None, created=created_time.isoformat(), file_path=file_path)

        assert content.id == uuid7_id
        assert content.title is None
        assert content.created == created_time.isoformat()
        assert content.file_path == file_path

    def test_freeform_content_initialization_with_title(self) -> None:
        """Contract: FreeformContent can be created with optional title."""
        uuid7_id = '0192f0c1-2345-7123-8abc-def012345678'
        created_time = datetime.fromisoformat('2025-09-20T15:30:00+00:00')
        file_path = Path('20250920T1530_0192f0c1-2345-7123-8abc-def012345678.md')
        title = 'Character Development Ideas'

        content = FreeformContent(id=uuid7_id, title=title, created=created_time.isoformat(), file_path=file_path)

        assert content.id == uuid7_id
        assert content.title == title
        assert content.created == created_time.isoformat()
        assert content.file_path == file_path

    def test_freeform_content_id_validation(self) -> None:
        """Contract: FreeformContent ID must be valid UUIDv7 format."""
        valid_uuid7 = '0192f0c1-2345-7123-8abc-def012345678'
        created_time = datetime.fromisoformat('2025-09-20T15:30:00+00:00')
        file_path = Path('20250920T1530_0192f0c1-2345-7123-8abc-def012345678.md')

        # Valid UUIDv7 should work
        content = FreeformContent(id=valid_uuid7, title=None, created=created_time.isoformat(), file_path=file_path)
        assert content.id == valid_uuid7

        # Invalid UUID formats should be rejected
        invalid_uuids = [
            'not-a-uuid',
            '12345',
            '',
            '550e8400-e29b-41d4-a716-446655440000',  # Valid UUID4 but not UUID7
        ]

        for invalid_uuid in invalid_uuids:
            with pytest.raises(FreeformContentValidationError):
                FreeformContent(id=invalid_uuid, title=None, created=created_time.isoformat(), file_path=file_path)

    def test_freeform_content_title_optional(self) -> None:
        """Contract: Title is optional for freeform content."""
        uuid7_id = '0192f0c1-2345-7123-8abc-def012345678'
        created_time = datetime.fromisoformat('2025-09-20T15:30:00+00:00')
        file_path = Path('20250920T1530_0192f0c1-2345-7123-8abc-def012345678.md')

        # None title should be allowed
        content_no_title = FreeformContent(
            id=uuid7_id, title=None, created=created_time.isoformat(), file_path=file_path
        )
        assert content_no_title.title is None

        # Empty string title should be converted to None or rejected
        content_empty_title = FreeformContent(
            id=uuid7_id, title='', created=created_time.isoformat(), file_path=file_path
        )
        # Either should be None or raise validation error
        assert content_empty_title.title is None or content_empty_title.title == ''

        # Valid title should be allowed
        content_with_title = FreeformContent(
            id=uuid7_id, title='Valid Title', created=created_time.isoformat(), file_path=file_path
        )
        assert content_with_title.title == 'Valid Title'

    def test_freeform_content_created_timestamp_validation(self) -> None:
        """Contract: Created timestamp must be valid datetime object."""
        uuid7_id = '0192f0c1-2345-7123-8abc-def012345678'
        valid_datetime = datetime.fromisoformat('2025-09-20T15:30:00+00:00')
        file_path = Path('20250920T1530_0192f0c1-2345-7123-8abc-def012345678.md')

        # Valid datetime should work
        content = FreeformContent(id=uuid7_id, title=None, created=valid_datetime.isoformat(), file_path=file_path)
        assert content.created == valid_datetime.isoformat()

        # None should be rejected
        with pytest.raises((TypeError, FreeformContentValidationError)):
            FreeformContent(
                id=uuid7_id,
                title=None,
                created=None,  # type: ignore[arg-type]
                file_path=file_path,
            )

    def test_freeform_content_filename_pattern_validation(self) -> None:
        """Contract: Filename must follow YYYYMMDDTHHMM_{uuid7}.md pattern."""
        uuid7_id = '0192f0c1-2345-7123-8abc-def012345678'
        created_time = datetime.fromisoformat('2025-09-20T15:30:00+00:00')

        # Valid filename pattern should work
        valid_filename = '20250920T1530_0192f0c1-2345-7123-8abc-def012345678.md'
        valid_path = Path(valid_filename)

        content = FreeformContent(id=uuid7_id, title=None, created=created_time.isoformat(), file_path=valid_path)
        assert content.file_path == valid_path

        # Invalid filename patterns should be rejected
        invalid_filenames = [
            'invalid.md',
            '20250920_0192f0c1-2345-7123-8abc-def012345678.md',  # Missing T and time
            '20250920T1530-0192f0c1-2345-7123-8abc-def012345678.md',  # Wrong separator
            '20250920T1530_wrong-uuid.md',  # Invalid UUID
            '20250920T1530_0192f0c1-2345-7123-8abc-def012345678.txt',  # Wrong extension
        ]

        for invalid_filename in invalid_filenames:
            with pytest.raises(FreeformContentValidationError):
                FreeformContent(
                    id=uuid7_id, title=None, created=created_time.isoformat(), file_path=Path(invalid_filename)
                )

    def test_freeform_content_filename_timestamp_consistency(self) -> None:
        """Contract: Filename timestamp must match created timestamp."""
        uuid7_id = '0192f0c1-2345-7123-8abc-def012345678'
        created_time = datetime.fromisoformat('2025-09-20T15:30:00+00:00')

        # Matching timestamp should work
        matching_filename = '20250920T1530_0192f0c1-2345-7123-8abc-def012345678.md'
        content = FreeformContent(
            id=uuid7_id, title=None, created=created_time.isoformat(), file_path=Path(matching_filename)
        )
        assert content.file_path.name == matching_filename

        # Non-matching timestamp should be rejected
        mismatched_filename = '20250920T1600_0192f0c1-2345-7123-8abc-def012345678.md'
        with pytest.raises(FreeformContentValidationError):
            FreeformContent(
                id=uuid7_id, title=None, created=created_time.isoformat(), file_path=Path(mismatched_filename)
            )

    def test_freeform_content_filename_uuid_consistency(self) -> None:
        """Contract: Filename UUID must match content ID."""
        uuid7_id = '0192f0c1-2345-7123-8abc-def012345678'
        created_time = datetime.fromisoformat('2025-09-20T15:30:00+00:00')

        # Matching UUID should work
        matching_filename = '20250920T1530_0192f0c1-2345-7123-8abc-def012345678.md'
        content = FreeformContent(
            id=uuid7_id, title=None, created=created_time.isoformat(), file_path=Path(matching_filename)
        )
        assert content.id == uuid7_id

        # Non-matching UUID should be rejected
        mismatched_filename = '20250920T1530_0192f0c1-2345-7456-8abc-def012345678.md'
        with pytest.raises(FreeformContentValidationError):
            FreeformContent(
                id=uuid7_id,  # Different from filename UUID
                title=None,
                created=created_time.isoformat(),
                file_path=Path(mismatched_filename),
            )

    def test_freeform_content_get_expected_filename(self) -> None:
        """Contract: Should provide method to get expected filename from ID and timestamp."""
        uuid7_id = '0192f0c1-2345-7123-8abc-def012345678'
        created_time = datetime.fromisoformat('2025-09-20T15:30:00+00:00')
        file_path = Path('20250920T1530_0192f0c1-2345-7123-8abc-def012345678.md')

        content = FreeformContent(id=uuid7_id, title=None, created=created_time.isoformat(), file_path=file_path)

        expected_filename = content.get_expected_filename()
        assert expected_filename == '20250920T1530_0192f0c1-2345-7123-8abc-def012345678.md'

    def test_freeform_content_parse_filename_components(self) -> None:
        """Contract: Should provide method to parse filename components."""
        uuid7_id = '0192f0c1-2345-7123-8abc-def012345678'
        created_time = datetime.fromisoformat('2025-09-20T15:30:00+00:00')
        file_path = Path('20250920T1530_0192f0c1-2345-7123-8abc-def012345678.md')

        content = FreeformContent(id=uuid7_id, title=None, created=created_time.isoformat(), file_path=file_path)

        components = content.parse_filename()
        assert components['timestamp'] == '20250920T1530'
        assert components['uuid'] == uuid7_id
        assert components['extension'] == '.md'

    def test_freeform_content_immutable_id(self) -> None:
        """Contract: Content ID must be immutable after creation."""
        uuid7_id = '0192f0c1-2345-7123-8abc-def012345678'
        created_time = datetime.fromisoformat('2025-09-20T15:30:00+00:00')
        file_path = Path('20250920T1530_0192f0c1-2345-7123-8abc-def012345678.md')

        content = FreeformContent(id=uuid7_id, title=None, created=created_time.isoformat(), file_path=file_path)

        # Should not be able to modify the ID
        with pytest.raises(AttributeError):
            content.id = 'different-id'  # type: ignore[misc]

    def test_freeform_content_immutable_created_timestamp(self) -> None:
        """Contract: Created timestamp must be immutable after creation."""
        uuid7_id = '0192f0c1-2345-7123-8abc-def012345678'
        created_time = datetime.fromisoformat('2025-09-20T15:30:00+00:00')
        file_path = Path('20250920T1530_0192f0c1-2345-7123-8abc-def012345678.md')

        content = FreeformContent(id=uuid7_id, title=None, created=created_time.isoformat(), file_path=file_path)

        # Should not be able to modify created timestamp
        with pytest.raises(AttributeError):
            content.created = datetime.fromisoformat('2025-09-20T16:00:00+00:00')  # type: ignore[assignment,misc]

    def test_freeform_content_update_title(self) -> None:
        """Contract: Should provide method to update title."""
        uuid7_id = '0192f0c1-2345-7123-8abc-def012345678'
        created_time = datetime.fromisoformat('2025-09-20T15:30:00+00:00')
        file_path = Path('20250920T1530_0192f0c1-2345-7123-8abc-def012345678.md')

        content = FreeformContent(id=uuid7_id, title=None, created=created_time.isoformat(), file_path=file_path)

        assert content.title is None

        # Should be able to update title
        new_title = 'Updated Title'
        content.update_title(new_title)

        assert content.title == new_title

        # Should be able to clear title
        content.update_title(None)
        assert content.title is None

    def test_freeform_content_equality_semantics(self) -> None:
        """Contract: Equality should be based on content ID."""
        uuid7_id = '0192f0c1-2345-7123-8abc-def012345678'
        created_time = datetime.fromisoformat('2025-09-20T15:30:00+00:00')
        file_path = Path('20250920T1530_0192f0c1-2345-7123-8abc-def012345678.md')

        content1 = FreeformContent(id=uuid7_id, title='Title 1', created=created_time.isoformat(), file_path=file_path)

        content2 = FreeformContent(
            id=uuid7_id,
            title='Title 2',  # Different title
            created=created_time.isoformat(),
            file_path=file_path,
        )

        # Same ID should make them equal despite different title
        assert content1 == content2

        # Different ID should make them different
        different_uuid = '0192f0c1-2345-7456-8abc-def012345678'
        different_file_path = Path('20250920T1530_0192f0c1-2345-7456-8abc-def012345678.md')
        content3 = FreeformContent(
            id=different_uuid, title='Title 1', created=created_time.isoformat(), file_path=different_file_path
        )

        assert content1 != content3

    def test_freeform_content_hashable_contract(self) -> None:
        """Contract: FreeformContent should be hashable based on ID."""
        uuid7_id = '0192f0c1-2345-7123-8abc-def012345678'
        created_time = datetime.fromisoformat('2025-09-20T15:30:00+00:00')
        file_path = Path('20250920T1530_0192f0c1-2345-7123-8abc-def012345678.md')

        content1 = FreeformContent(id=uuid7_id, title='Title 1', created=created_time.isoformat(), file_path=file_path)

        content2 = FreeformContent(id=uuid7_id, title='Title 2', created=created_time.isoformat(), file_path=file_path)

        # Same ID should have same hash
        assert hash(content1) == hash(content2)

        # Should be usable in sets
        content_set = {content1, content2}
        assert len(content_set) == 1

    def test_freeform_content_string_representation(self) -> None:
        """Contract: Should have meaningful string representation."""
        uuid7_id = '0192f0c1-2345-7123-8abc-def012345678'
        created_time = datetime.fromisoformat('2025-09-20T15:30:00+00:00')
        file_path = Path('20250920T1530_0192f0c1-2345-7123-8abc-def012345678.md')

        content_with_title = FreeformContent(
            id=uuid7_id, title='Character Development Ideas', created=created_time.isoformat(), file_path=file_path
        )

        str_repr = str(content_with_title)
        assert 'Character Development Ideas' in str_repr

        # Content without title should show filename or ID
        content_without_title = FreeformContent(
            id=uuid7_id, title=None, created=created_time.isoformat(), file_path=file_path
        )

        str_repr_no_title = str(content_without_title)
        assert '20250920T1530' in str_repr_no_title or uuid7_id[:8] in str_repr_no_title

    def test_freeform_content_filename_pattern_regex(self) -> None:
        """Contract: Should provide regex pattern for validating filenames."""
        pattern = FreeformContent.get_filename_pattern()

        # Valid filenames should match
        valid_filenames = [
            '20250920T1530_0192f0c1-2345-7123-8abc-def012345678.md',
            '20251231T2359_0192f0c1-2345-7123-8abc-def012345678.md',
            '20250101T0000_0192f0c1-2345-7123-8abc-def012345678.md',
        ]

        for filename in valid_filenames:
            assert re.match(pattern, filename), f'Pattern should match {filename}'

        # Invalid filenames should not match
        invalid_filenames = [
            'invalid.md',
            '20250920_0192f0c1-2345-7123-8abc-def012345678.md',
            '20250920T1530-0192f0c1-2345-7123-8abc-def012345678.md',
            '20250920T1530_invalid-uuid.md',
            '20250920T1530_0192f0c1-2345-7123-8abc-def012345678.txt',
        ]

        for filename in invalid_filenames:
            assert not re.match(pattern, filename), f'Pattern should not match {filename}'


@pytest.fixture
def sample_uuid7() -> str:
    """Fixture providing a sample UUIDv7."""
    return '0192f0c1-2345-7123-8abc-def012345678'


@pytest.fixture
def sample_created_time() -> datetime:
    """Fixture providing a sample creation timestamp."""
    return datetime.fromisoformat('2025-09-20T15:30:00+00:00')


@pytest.fixture
def sample_file_path(sample_uuid7: str) -> Path:
    """Fixture providing a sample file path."""
    return Path(f'20250920T1530_{sample_uuid7}.md')


@pytest.fixture
def minimal_freeform_content(
    sample_uuid7: str, sample_created_time: datetime, sample_file_path: Path
) -> FreeformContent:
    """Fixture providing minimal FreeformContent."""
    return FreeformContent(
        id=sample_uuid7, title=None, created=sample_created_time.isoformat(), file_path=sample_file_path
    )


@pytest.fixture
def complete_freeform_content(
    sample_uuid7: str, sample_created_time: datetime, sample_file_path: Path
) -> FreeformContent:
    """Fixture providing complete FreeformContent with title."""
    return FreeformContent(
        id=sample_uuid7,
        title='Character Development Ideas',
        created=sample_created_time.isoformat(),
        file_path=sample_file_path,
    )
