"""Tests for other domain value objects."""

from datetime import UTC, datetime

import pytest
from uuid_extension import uuid7

from prosemark.domain.value_objects import NodeId, NodeMetadata, Timestamp


class TestTimestamp:
    """Test suite for Timestamp value object."""

    def test_create_from_valid_iso_string(self) -> None:
        """Timestamp accepts valid ISO8601 strings."""
        iso_str = '2025-09-10T10:00:00Z'
        timestamp = Timestamp(iso_str)

        assert timestamp.value == iso_str
        assert str(timestamp) == iso_str

    def test_create_from_datetime(self) -> None:
        """Timestamp accepts datetime objects and converts to UTC ISO string."""
        dt = datetime(2025, 9, 10, 10, 0, 0, tzinfo=UTC)
        timestamp = Timestamp(dt)

        expected = '2025-09-10T10:00:00+00:00'
        assert timestamp.value == expected

    def test_rejects_invalid_iso_format(self) -> None:
        """Timestamp rejects invalid ISO8601 formats."""
        invalid_timestamps = [
            'not-a-date',
            '2025-13-45',  # Invalid month/day
            '',
            '2025-02-30T10:00:00',  # Invalid date (Feb 30th)
        ]

        for invalid_ts in invalid_timestamps:
            with pytest.raises(ValueError, match='Invalid timestamp'):
                Timestamp(invalid_ts)

    def test_accepts_various_iso_formats(self) -> None:
        """Timestamp accepts various valid ISO8601 formats."""
        valid_timestamps = [
            '2025-09-10T10:00:00Z',
            '2025-09-10T10:00:00+00:00',
            '2025-09-10T10:00:00-07:00',
            '2025-09-10T10:00:00.123Z',
            '2025-09-10T10:00:00.123456+00:00',
        ]

        for valid_ts in valid_timestamps:
            timestamp = Timestamp(valid_ts)
            assert timestamp.value == valid_ts

    def test_immutability(self) -> None:
        """Timestamp is immutable."""
        timestamp = Timestamp('2025-09-10T10:00:00Z')

        with pytest.raises(AttributeError):
            timestamp.value = '2025-09-11T10:00:00Z'  # type: ignore[misc]

    def test_equality(self) -> None:
        """Timestamp equality is based on value."""
        ts1 = Timestamp('2025-09-10T10:00:00Z')
        ts2 = Timestamp('2025-09-10T10:00:00Z')
        ts3 = Timestamp('2025-09-11T10:00:00Z')

        assert ts1 == ts2
        assert ts1 != ts3
        assert ts1 != '2025-09-10T10:00:00Z'  # Should not equal plain string

    def test_ordering(self) -> None:
        """Timestamp supports chronological ordering."""
        ts1 = Timestamp('2025-09-10T10:00:00Z')
        ts2 = Timestamp('2025-09-10T11:00:00Z')
        ts3 = Timestamp('2025-09-11T10:00:00Z')

        assert ts1 < ts2 < ts3
        assert ts3 > ts2 > ts1
        assert ts1 <= ts2 <= ts3
        assert ts3 >= ts2 >= ts1

    def test_hashable(self) -> None:
        """Timestamp is hashable."""
        ts1 = Timestamp('2025-09-10T10:00:00Z')
        ts2 = Timestamp('2025-09-10T10:00:00Z')
        ts3 = Timestamp('2025-09-11T10:00:00Z')

        ts_set = {ts1, ts2, ts3}
        assert len(ts_set) == 2  # ts1 and ts2 are the same

    def test_to_datetime(self) -> None:
        """Timestamp can be converted back to datetime."""
        iso_str = '2025-09-10T10:00:00Z'
        timestamp = Timestamp(iso_str)

        dt = timestamp.to_datetime()
        assert isinstance(dt, datetime)
        assert dt.tzinfo is not None  # Should have timezone info

    def test_repr(self) -> None:
        """Timestamp has a useful repr."""
        ts = Timestamp('2025-09-10T10:00:00Z')
        assert repr(ts) == "Timestamp('2025-09-10T10:00:00Z')"


class TestNodeMetadata:
    """Test suite for NodeMetadata value object."""

    def test_create_complete_metadata(self) -> None:
        """NodeMetadata can be created with all fields."""
        node_id = NodeId(uuid7())
        created = Timestamp('2025-09-10T10:00:00Z')
        updated = Timestamp('2025-09-10T11:00:00Z')

        metadata = NodeMetadata(
            id=node_id, title='Chapter 1', synopsis='This is the synopsis', created=created, updated=updated
        )

        assert metadata.id == node_id
        assert metadata.title == 'Chapter 1'
        assert metadata.synopsis == 'This is the synopsis'
        assert metadata.created == created
        assert metadata.updated == updated

    def test_create_minimal_metadata(self) -> None:
        """NodeMetadata can be created with minimal fields."""
        node_id = NodeId(uuid7())
        created = Timestamp('2025-09-10T10:00:00Z')

        metadata = NodeMetadata(id=node_id, title=None, synopsis=None, created=created, updated=created)

        assert metadata.id == node_id
        assert metadata.title is None
        assert metadata.synopsis is None
        assert metadata.created == created
        assert metadata.updated == created

    def test_immutability(self) -> None:
        """NodeMetadata is immutable."""
        node_id = NodeId(uuid7())
        created = Timestamp('2025-09-10T10:00:00Z')

        metadata = NodeMetadata(
            id=node_id, title='Original', synopsis='Original synopsis', created=created, updated=created
        )

        # Should not be able to modify attributes
        with pytest.raises(AttributeError):
            metadata.title = 'Modified'

        with pytest.raises(AttributeError):
            metadata.id = NodeId(uuid7())

    def test_equality(self) -> None:
        """NodeMetadata equality is based on all attributes."""
        node_id = NodeId(uuid7())
        created = Timestamp('2025-09-10T10:00:00Z')

        metadata1 = NodeMetadata(id=node_id, title='Chapter 1', synopsis='Synopsis', created=created, updated=created)

        metadata2 = NodeMetadata(id=node_id, title='Chapter 1', synopsis='Synopsis', created=created, updated=created)

        metadata3 = NodeMetadata(
            id=node_id, title='Different Title', synopsis='Synopsis', created=created, updated=created
        )

        assert metadata1 == metadata2
        assert metadata1 != metadata3

    def test_with_updated_timestamp(self) -> None:
        """Can create updated copy with new timestamp."""
        node_id = NodeId(uuid7())
        created = Timestamp('2025-09-10T10:00:00Z')
        updated = Timestamp('2025-09-10T11:00:00Z')

        original = NodeMetadata(id=node_id, title='Chapter 1', synopsis='Synopsis', created=created, updated=created)

        updated_metadata = original.with_updated(updated)

        assert updated_metadata.id == original.id
        assert updated_metadata.title == original.title
        assert updated_metadata.synopsis == original.synopsis
        assert updated_metadata.created == original.created
        assert updated_metadata.updated == updated
        # Original should be unchanged
        assert original.updated == created

    def test_with_modified_title(self) -> None:
        """Can create modified copy with new title."""
        node_id = NodeId(uuid7())
        created = Timestamp('2025-09-10T10:00:00Z')

        original = NodeMetadata(
            id=node_id, title='Original Title', synopsis='Synopsis', created=created, updated=created
        )

        modified = original.with_title('New Title')

        assert modified.title == 'New Title'
        assert modified.id == original.id
        assert modified.synopsis == original.synopsis
        assert modified.created == original.created
        # Should also update the timestamp
        assert modified.updated != original.updated

    def test_with_modified_synopsis(self) -> None:
        """Can create modified copy with new synopsis."""
        node_id = NodeId(uuid7())
        created = Timestamp('2025-09-10T10:00:00Z')

        original = NodeMetadata(
            id=node_id, title='Title', synopsis='Original synopsis', created=created, updated=created
        )

        modified = original.with_synopsis('New synopsis')

        assert modified.synopsis == 'New synopsis'
        assert modified.id == original.id
        assert modified.title == original.title
        assert modified.created == original.created
        # Should also update the timestamp
        assert modified.updated != original.updated

    def test_to_frontmatter_dict(self) -> None:
        """Can convert to frontmatter dictionary."""
        node_id = NodeId(uuid7())
        created = Timestamp('2025-09-10T10:00:00Z')
        updated = Timestamp('2025-09-10T11:00:00Z')

        metadata = NodeMetadata(
            id=node_id, title='Chapter 1', synopsis='Multi-line\nsynopsis\ntext', created=created, updated=updated
        )

        frontmatter = metadata.to_frontmatter_dict()

        assert frontmatter['id'] == str(node_id)
        assert frontmatter['title'] == 'Chapter 1'
        assert frontmatter['synopsis'] == 'Multi-line\nsynopsis\ntext'
        assert frontmatter['created'] == str(created)
        assert frontmatter['updated'] == str(updated)

    def test_from_frontmatter_dict(self) -> None:
        """Can create from frontmatter dictionary."""
        node_id_str = str(NodeId(uuid7()))

        frontmatter = {
            'id': node_id_str,
            'title': 'Chapter 1',
            'synopsis': 'Synopsis text',
            'created': '2025-09-10T10:00:00Z',
            'updated': '2025-09-10T11:00:00Z',
        }

        metadata = NodeMetadata.from_frontmatter_dict(frontmatter)

        assert str(metadata.id) == node_id_str
        assert metadata.title == 'Chapter 1'
        assert metadata.synopsis == 'Synopsis text'
        assert str(metadata.created) == '2025-09-10T10:00:00Z'
        assert str(metadata.updated) == '2025-09-10T11:00:00Z'

    def test_from_frontmatter_handles_missing_fields(self) -> None:
        """from_frontmatter_dict handles missing optional fields."""
        node_id_str = str(NodeId(uuid7()))

        frontmatter = {'id': node_id_str, 'created': '2025-09-10T10:00:00Z', 'updated': '2025-09-10T11:00:00Z'}

        metadata = NodeMetadata.from_frontmatter_dict(frontmatter)

        assert str(metadata.id) == node_id_str
        assert metadata.title is None
        assert metadata.synopsis is None

    def test_repr(self) -> None:
        """NodeMetadata has a useful repr."""
        node_id = NodeId(uuid7())
        created = Timestamp('2025-09-10T10:00:00Z')

        metadata = NodeMetadata(id=node_id, title='Chapter 1', synopsis='Synopsis', created=created, updated=created)

        repr_str = repr(metadata)
        assert 'NodeMetadata' in repr_str
        assert 'Chapter 1' in repr_str
