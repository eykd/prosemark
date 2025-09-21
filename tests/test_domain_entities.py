"""Tests for domain entities."""

from datetime import UTC, datetime
from pathlib import Path

import pytest

from prosemark.domain.entities import FreeformContent, Node
from prosemark.domain.models import NodeId
from prosemark.exceptions import FreeformContentValidationError, NodeValidationError


class TestNode:
    """Test Node entity."""

    def setup_method(self) -> None:
        """Set up test data."""
        self.valid_node_id = NodeId('0192f0c1-2345-7123-8abc-def012345678')
        self.created_time = datetime(2023, 1, 1, 12, 0, 0, tzinfo=UTC)
        self.updated_time = datetime(2023, 1, 2, 12, 0, 0, tzinfo=UTC)
        self.draft_path = Path('/test/node.md')
        self.notes_path = Path('/test/node.notes.md')

    def test_node_creation_with_valid_data(self) -> None:
        """Test successful node creation with valid data."""
        node = Node(
            node_id=self.valid_node_id,
            title='Test Node',
            synopsis='Test Synopsis',
            created=self.created_time,
            updated=self.updated_time,
            draft_path=self.draft_path,
            notes_path=self.notes_path,
        )

        assert node.id == self.valid_node_id
        assert node.title == 'Test Node'
        assert node.synopsis == 'Test Synopsis'
        assert node.created == self.created_time
        assert node.updated == self.updated_time
        assert node.draft_path == self.draft_path
        assert node.notes_path == self.notes_path

    def test_node_creation_with_string_timestamps(self) -> None:
        """Test node creation with string timestamps."""
        node = Node(
            node_id=self.valid_node_id,
            title='Test Node',
            synopsis='Test Synopsis',
            created='2023-01-01T12:00:00+00:00',
            updated='2023-01-02T12:00:00+00:00',
            draft_path=self.draft_path,
            notes_path=self.notes_path,
        )

        assert isinstance(node.created, datetime)
        assert isinstance(node.updated, datetime)

    def test_node_creation_none_node_id(self) -> None:
        """Test node creation with None node_id raises error."""
        with pytest.raises(NodeValidationError, match='node_id cannot be None'):
            Node(
                node_id=None,  # type: ignore[arg-type]
                title='Test Node',
                synopsis='Test Synopsis',
                created=self.created_time,
                updated=self.updated_time,
                draft_path=self.draft_path,
                notes_path=self.notes_path,
            )

    def test_node_creation_none_draft_path(self) -> None:
        """Test node creation with None draft_path raises error."""
        with pytest.raises(NodeValidationError, match='draft_path cannot be None'):
            Node(
                node_id=self.valid_node_id,
                title='Test Node',
                synopsis='Test Synopsis',
                created=self.created_time,
                updated=self.updated_time,
                draft_path=None,  # type: ignore[arg-type]
                notes_path=self.notes_path,
            )

    def test_node_creation_none_notes_path(self) -> None:
        """Test node creation with None notes_path raises error."""
        with pytest.raises(NodeValidationError, match='notes_path cannot be None'):
            Node(
                node_id=self.valid_node_id,
                title='Test Node',
                synopsis='Test Synopsis',
                created=self.created_time,
                updated=self.updated_time,
                draft_path=self.draft_path,
                notes_path=None,  # type: ignore[arg-type]
            )

    def test_node_creation_updated_before_created(self) -> None:
        """Test node creation with updated before created raises error."""
        with pytest.raises(NodeValidationError, match='Updated timestamp must be >= created timestamp'):
            Node(
                node_id=self.valid_node_id,
                title='Test Node',
                synopsis='Test Synopsis',
                created=self.updated_time,  # Later time
                updated=self.created_time,  # Earlier time
                draft_path=self.draft_path,
                notes_path=self.notes_path,
            )

    def test_touch_with_default_time(self) -> None:
        """Test touch method with default current time."""
        node = Node(
            node_id=self.valid_node_id,
            title='Test Node',
            synopsis='Test Synopsis',
            created=self.created_time,
            updated=self.created_time,
            draft_path=self.draft_path,
            notes_path=self.notes_path,
        )

        original_updated = node.updated
        node.touch()

        # Should be updated to a more recent time
        assert node.updated > original_updated

    def test_touch_with_specific_time(self) -> None:
        """Test touch method with specific time."""
        node = Node(
            node_id=self.valid_node_id,
            title='Test Node',
            synopsis='Test Synopsis',
            created=self.created_time,
            updated=self.created_time,
            draft_path=self.draft_path,
            notes_path=self.notes_path,
        )

        new_time = datetime(2023, 6, 15, 10, 30, 0, tzinfo=UTC)
        node.touch(new_time)

        assert node.updated == new_time

    def test_touch_with_string_time(self) -> None:
        """Test touch method with string time."""
        node = Node(
            node_id=self.valid_node_id,
            title='Test Node',
            synopsis='Test Synopsis',
            created=self.created_time,
            updated=self.created_time,
            draft_path=self.draft_path,
            notes_path=self.notes_path,
        )

        time_str = '2023-06-15T10:30:00+00:00'
        node.touch(time_str)

        assert node.updated == datetime.fromisoformat(time_str)

    def test_update_metadata_title_only(self) -> None:
        """Test updating only title."""
        node = Node(
            node_id=self.valid_node_id,
            title='Old Title',
            synopsis='Old Synopsis',
            created=self.created_time,
            updated=self.created_time,
            draft_path=self.draft_path,
            notes_path=self.notes_path,
        )

        node.update_metadata(title='New Title')

        assert node.title == 'New Title'
        assert node.synopsis == 'Old Synopsis'  # Unchanged
        # updated timestamp unchanged when no explicit timestamp provided
        assert node.updated == self.created_time

    def test_update_metadata_synopsis_only(self) -> None:
        """Test updating only synopsis."""
        node = Node(
            node_id=self.valid_node_id,
            title='Test Title',
            synopsis='Old Synopsis',
            created=self.created_time,
            updated=self.created_time,
            draft_path=self.draft_path,
            notes_path=self.notes_path,
        )

        node.update_metadata(synopsis='New Synopsis')

        assert node.title == 'Test Title'  # Unchanged
        assert node.synopsis == 'New Synopsis'

    def test_update_metadata_both_with_time(self) -> None:
        """Test updating both title and synopsis with specific time."""
        node = Node(
            node_id=self.valid_node_id,
            title='Old Title',
            synopsis='Old Synopsis',
            created=self.created_time,
            updated=self.created_time,
            draft_path=self.draft_path,
            notes_path=self.notes_path,
        )

        new_time = datetime(2023, 12, 25, 15, 0, 0, tzinfo=UTC)
        node.update_metadata(title='New Title', synopsis='New Synopsis', updated=new_time)

        assert node.title == 'New Title'
        assert node.synopsis == 'New Synopsis'
        assert node.updated == new_time

    def test_update_metadata_no_changes(self) -> None:
        """Test update_metadata with no changes."""
        node = Node(
            node_id=self.valid_node_id,
            title='Test Title',
            synopsis='Test Synopsis',
            created=self.created_time,
            updated=self.created_time,
            draft_path=self.draft_path,
            notes_path=self.notes_path,
        )

        node.update_metadata()

        # With no changes and no explicit timestamp, values should remain unchanged
        assert node.title == 'Test Title'
        assert node.synopsis == 'Test Synopsis'
        assert node.updated == self.created_time

    def test_node_to_metadata(self) -> None:
        """Test Node.to_metadata method."""
        node = Node(
            node_id=self.valid_node_id,
            title='Test Title',
            synopsis='Test Synopsis',
            created=self.created_time,
            updated=self.updated_time,
            draft_path=self.draft_path,
            notes_path=self.notes_path,
        )

        metadata = node.to_metadata()

        assert metadata.id == self.valid_node_id
        assert metadata.title == 'Test Title'
        assert metadata.synopsis == 'Test Synopsis'
        assert metadata.created == self.created_time
        assert metadata.updated == self.updated_time

    def test_node_str_with_title(self) -> None:
        """Test Node.__str__ with title."""
        node = Node(
            node_id=self.valid_node_id,
            title='Test Title',
            synopsis='Test Synopsis',
            created=self.created_time,
            updated=self.updated_time,
            draft_path=self.draft_path,
            notes_path=self.notes_path,
        )

        assert str(node) == 'Node(Test Title)'

    def test_node_str_without_title(self) -> None:
        """Test Node.__str__ without title."""
        node = Node(
            node_id=self.valid_node_id,
            title=None,
            synopsis='Test Synopsis',
            created=self.created_time,
            updated=self.updated_time,
            draft_path=self.draft_path,
            notes_path=self.notes_path,
        )

        assert str(node) == f'Node({self.valid_node_id})'

    def test_node_equality(self) -> None:
        """Test Node equality based on ID."""
        node1 = Node(
            node_id=self.valid_node_id,
            title='Title 1',
            synopsis='Synopsis 1',
            created=self.created_time,
            updated=self.updated_time,
            draft_path=self.draft_path,
            notes_path=self.notes_path,
        )

        node2 = Node(
            node_id=self.valid_node_id,
            title='Title 2',  # Different title
            synopsis='Synopsis 2',  # Different synopsis
            created=self.created_time,
            updated=self.updated_time,
            draft_path=Path('/different/path.md'),  # Different path
            notes_path=Path('/different/notes.md'),  # Different path
        )

        assert node1 == node2  # Should be equal because same ID

    def test_node_inequality(self) -> None:
        """Test Node inequality with different IDs."""
        other_node_id = NodeId('0192f0c1-2345-7123-8abc-def012345679')

        node1 = Node(
            node_id=self.valid_node_id,
            title='Title',
            synopsis='Synopsis',
            created=self.created_time,
            updated=self.updated_time,
            draft_path=self.draft_path,
            notes_path=self.notes_path,
        )

        node2 = Node(
            node_id=other_node_id,
            title='Title',
            synopsis='Synopsis',
            created=self.created_time,
            updated=self.updated_time,
            draft_path=self.draft_path,
            notes_path=self.notes_path,
        )

        assert node1 != node2
        assert node1 != 'not a node'

    def test_node_hash(self) -> None:
        """Test Node hashing based on ID."""
        node1 = Node(
            node_id=self.valid_node_id,
            title='Title 1',
            synopsis='Synopsis 1',
            created=self.created_time,
            updated=self.updated_time,
            draft_path=self.draft_path,
            notes_path=self.notes_path,
        )

        node2 = Node(
            node_id=self.valid_node_id,
            title='Title 2',  # Different attributes
            synopsis='Synopsis 2',
            created=self.created_time,
            updated=self.updated_time,
            draft_path=self.draft_path,
            notes_path=self.notes_path,
        )

        assert hash(node1) == hash(node2)  # Same ID, same hash


class TestFreeformContent:
    """Test FreeformContent entity."""

    def setup_method(self) -> None:
        """Set up test data."""
        self.valid_uuid = '0192f0c1-2345-7123-8abc-def012345678'
        self.valid_timestamp = '2023-01-15T14:30:00+00:00'
        self.valid_filename = '20230115T1430_0192f0c1-2345-7123-8abc-def012345678.md'
        self.valid_file_path = Path(f'/test/{self.valid_filename}')

    def test_freeform_content_creation_valid(self) -> None:
        """Test successful FreeformContent creation."""
        content = FreeformContent(
            id=self.valid_uuid,
            title='Test Content',
            created=self.valid_timestamp,
            file_path=self.valid_file_path,
        )

        assert content.id == self.valid_uuid
        assert content.title == 'Test Content'
        assert content.created == self.valid_timestamp
        assert content.file_path == self.valid_file_path

    def test_freeform_content_none_created(self) -> None:
        """Test FreeformContent with None created timestamp."""
        with pytest.raises(FreeformContentValidationError, match='created timestamp cannot be None'):
            FreeformContent(
                id=self.valid_uuid,
                title='Test Content',
                created=None,  # type: ignore[arg-type]
                file_path=self.valid_file_path,
            )

    def test_freeform_content_none_id(self) -> None:
        """Test FreeformContent with None ID."""
        with pytest.raises(FreeformContentValidationError, match='id cannot be None'):
            FreeformContent(
                id=None,  # type: ignore[arg-type]
                title='Test Content',
                created=self.valid_timestamp,
                file_path=self.valid_file_path,
            )

    def test_freeform_content_invalid_uuid_format(self) -> None:
        """Test FreeformContent with invalid UUID format."""
        invalid_file_path = Path('/test/20230115T1430_invalid-uuid.md')

        with pytest.raises(FreeformContentValidationError, match='Invalid UUID format'):
            FreeformContent(
                id='invalid-uuid',
                title='Test Content',
                created=self.valid_timestamp,
                file_path=invalid_file_path,
            )

    def test_freeform_content_invalid_uuid_version(self) -> None:
        """Test FreeformContent with non-UUIDv7."""
        # UUIDv4 for testing
        uuid_v4 = '550e8400-e29b-41d4-a716-446655440000'
        invalid_file_path = Path(f'/test/20230115T1430_{uuid_v4}.md')

        with pytest.raises(FreeformContentValidationError, match='must be UUIDv7, got version 4'):
            FreeformContent(
                id=uuid_v4,
                title='Test Content',
                created=self.valid_timestamp,
                file_path=invalid_file_path,
            )

    def test_freeform_content_file_not_md(self) -> None:
        """Test FreeformContent with non-.md file."""
        invalid_file_path = Path(f'/test/20230115T1430_{self.valid_uuid}.txt')

        with pytest.raises(FreeformContentValidationError, match=r'must end with \.md'):
            FreeformContent(
                id=self.valid_uuid,
                title='Test Content',
                created=self.valid_timestamp,
                file_path=invalid_file_path,
            )

    def test_freeform_content_filename_no_underscore(self) -> None:
        """Test FreeformContent with filename missing underscore."""
        invalid_file_path = Path(f'/test/20230115T1430{self.valid_uuid}.md')

        with pytest.raises(FreeformContentValidationError, match='must contain underscore'):
            FreeformContent(
                id=self.valid_uuid,
                title='Test Content',
                created=self.valid_timestamp,
                file_path=invalid_file_path,
            )

    def test_freeform_content_uuid_mismatch(self) -> None:
        """Test FreeformContent with UUID mismatch between ID and filename."""
        different_uuid = '0192f0c1-2345-7123-8abc-def012345679'
        invalid_file_path = Path(f'/test/20230115T1430_{different_uuid}.md')

        with pytest.raises(FreeformContentValidationError, match=r"UUID in filename.*doesn't match id"):
            FreeformContent(
                id=self.valid_uuid,
                title='Test Content',
                created=self.valid_timestamp,
                file_path=invalid_file_path,
            )

    def test_freeform_content_invalid_timestamp_format(self) -> None:
        """Test FreeformContent with invalid timestamp format in filename."""
        invalid_file_path = Path(f'/test/2023011T1430_{self.valid_uuid}.md')  # Missing digit

        with pytest.raises(FreeformContentValidationError, match='Invalid timestamp format'):
            FreeformContent(
                id=self.valid_uuid,
                title='Test Content',
                created=self.valid_timestamp,
                file_path=invalid_file_path,
            )

    def test_freeform_content_invalid_month(self) -> None:
        """Test FreeformContent with invalid month in timestamp."""
        invalid_file_path = Path(f'/test/20231315T1430_{self.valid_uuid}.md')  # Month 13

        with pytest.raises(FreeformContentValidationError, match='Invalid month'):
            FreeformContent(
                id=self.valid_uuid,
                title='Test Content',
                created=self.valid_timestamp,
                file_path=invalid_file_path,
            )

    def test_freeform_content_invalid_day(self) -> None:
        """Test FreeformContent with invalid day in timestamp."""
        invalid_file_path = Path(f'/test/20230132T1430_{self.valid_uuid}.md')  # Day 32

        with pytest.raises(FreeformContentValidationError, match='Invalid day'):
            FreeformContent(
                id=self.valid_uuid,
                title='Test Content',
                created=self.valid_timestamp,
                file_path=invalid_file_path,
            )

    def test_freeform_content_invalid_hour(self) -> None:
        """Test FreeformContent with invalid hour in timestamp."""
        invalid_file_path = Path(f'/test/20230115T2530_{self.valid_uuid}.md')  # Hour 25

        with pytest.raises(FreeformContentValidationError, match='Invalid hour'):
            FreeformContent(
                id=self.valid_uuid,
                title='Test Content',
                created=self.valid_timestamp,
                file_path=invalid_file_path,
            )

    def test_freeform_content_invalid_minute(self) -> None:
        """Test FreeformContent with invalid minute in timestamp."""
        invalid_file_path = Path(f'/test/20230115T1460_{self.valid_uuid}.md')  # Minute 60

        with pytest.raises(FreeformContentValidationError, match='Invalid minute'):
            FreeformContent(
                id=self.valid_uuid,
                title='Test Content',
                created=self.valid_timestamp,
                file_path=invalid_file_path,
            )

    def test_freeform_content_timestamp_mismatch(self) -> None:
        """Test FreeformContent with mismatched timestamp and filename."""
        # Different timestamp in filename
        invalid_file_path = Path(f'/test/20230115T1500_{self.valid_uuid}.md')  # 15:00 instead of 14:30

        with pytest.raises(
            FreeformContentValidationError, match=r'Filename timestamp.*does not match created timestamp'
        ):
            FreeformContent(
                id=self.valid_uuid,
                title='Test Content',
                created=self.valid_timestamp,
                file_path=invalid_file_path,
            )

    def test_get_expected_filename(self) -> None:
        """Test get_expected_filename method."""
        content = FreeformContent(
            id=self.valid_uuid,
            title='Test Content',
            created=self.valid_timestamp,
            file_path=self.valid_file_path,
        )

        expected = content.get_expected_filename()
        assert expected == self.valid_filename

    def test_parse_filename(self) -> None:
        """Test parse_filename method."""
        content = FreeformContent(
            id=self.valid_uuid,
            title='Test Content',
            created=self.valid_timestamp,
            file_path=self.valid_file_path,
        )

        result = content.parse_filename()
        assert result['timestamp'] == '20230115T1430'
        assert result['uuid'] == self.valid_uuid
        assert result['extension'] == '.md'

    def test_parse_filename_no_md_extension(self) -> None:
        """Test parse_filename with non-.md file."""
        invalid_file_path = Path(f'/test/{self.valid_uuid}.txt')
        content = FreeformContent(
            id=self.valid_uuid,
            title='Test Content',
            created=self.valid_timestamp,
            file_path=self.valid_file_path,
        )
        # Override file_path for this test
        object.__setattr__(content, 'file_path', invalid_file_path)

        with pytest.raises(FreeformContentValidationError, match=r'Filename must end with \.md'):
            content.parse_filename()

    def test_parse_filename_no_underscore(self) -> None:
        """Test parse_filename with no underscore in filename."""
        invalid_file_path = Path(f'/test/{self.valid_uuid}.md')
        content = FreeformContent(
            id=self.valid_uuid,
            title='Test Content',
            created=self.valid_timestamp,
            file_path=self.valid_file_path,
        )
        # Override file_path for this test
        object.__setattr__(content, 'file_path', invalid_file_path)

        with pytest.raises(FreeformContentValidationError, match='Filename must contain underscore'):
            content.parse_filename()

    def test_update_title(self) -> None:
        """Test update_title method."""
        content = FreeformContent(
            id=self.valid_uuid,
            title='Old Title',
            created=self.valid_timestamp,
            file_path=self.valid_file_path,
        )

        content.update_title('New Title')
        assert content.title == 'New Title'

        content.update_title(None)
        assert content.title is None

    def test_freeform_content_equality(self) -> None:
        """Test FreeformContent equality based on ID."""
        content1 = FreeformContent(
            id=self.valid_uuid,
            title='Title 1',
            created=self.valid_timestamp,
            file_path=self.valid_file_path,
        )

        content2 = FreeformContent(
            id=self.valid_uuid,
            title='Title 2',  # Different title
            created=self.valid_timestamp,
            file_path=self.valid_file_path,
        )

        assert content1 == content2  # Same ID

    def test_freeform_content_inequality(self) -> None:
        """Test FreeformContent inequality with different IDs."""
        different_uuid = '0192f0c1-2345-7123-8abc-def012345679'
        different_file_path = Path(f'/test/20230115T1430_{different_uuid}.md')

        content1 = FreeformContent(
            id=self.valid_uuid,
            title='Title',
            created=self.valid_timestamp,
            file_path=self.valid_file_path,
        )

        content2 = FreeformContent(
            id=different_uuid,
            title='Title',
            created=self.valid_timestamp,
            file_path=different_file_path,
        )

        assert content1 != content2
        assert content1 != 'not content'

    def test_freeform_content_hash(self) -> None:
        """Test FreeformContent hashing based on ID."""
        content1 = FreeformContent(
            id=self.valid_uuid,
            title='Title 1',
            created=self.valid_timestamp,
            file_path=self.valid_file_path,
        )

        content2 = FreeformContent(
            id=self.valid_uuid,
            title='Title 2',  # Different title
            created=self.valid_timestamp,
            file_path=self.valid_file_path,
        )

        assert hash(content1) == hash(content2)  # Same ID, same hash

    def test_get_filename_pattern(self) -> None:
        """Test get_filename_pattern class method."""
        pattern = FreeformContent.get_filename_pattern()
        assert isinstance(pattern, str)
        assert r'\d{8}T\d{4}' in pattern  # Should contain timestamp pattern
        assert r'[0-9a-f]{8}-[0-9a-f]{4}' in pattern  # Should contain UUID pattern
        assert r'\.md' in pattern  # Should include .md extension
