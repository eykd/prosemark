"""Contract tests for Node entity.

These tests define the behavioral contracts that any Node implementation must satisfy.
They will fail until the Node class is properly implemented.
"""

from datetime import datetime
from pathlib import Path

import pytest

# These imports will fail until classes are implemented
from prosemark.domain.entities import Node, NodeId
from prosemark.exceptions import NodeValidationError


class TestNodeContract:
    """Contract tests for Node entity."""

    def test_node_initialization_minimal(self) -> None:
        """Contract: Node can be created with minimal required fields."""
        node_id = NodeId('0192f0c1-2345-7123-8abc-def012345678')
        created_time = datetime.fromisoformat('2025-09-20T15:30:00+00:00')
        draft_path = Path('0192f0c1.md')
        notes_path = Path('0192f0c1.notes.md')

        node = Node(
            node_id=node_id,
            title=None,
            synopsis=None,
            created=created_time,
            updated=created_time,
            draft_path=draft_path,
            notes_path=notes_path,
        )

        assert node.id == node_id
        assert node.title is None
        assert node.synopsis is None
        assert node.created == created_time
        assert node.updated == created_time
        assert node.draft_path == draft_path
        assert node.notes_path == notes_path

    def test_node_initialization_complete(self) -> None:
        """Contract: Node can be created with all fields populated."""
        node_id = NodeId('0192f0c1-2345-7123-8abc-def012345678')
        created_time = datetime.fromisoformat('2025-09-20T15:30:00+00:00')
        updated_time = datetime.fromisoformat('2025-09-20T16:45:00+00:00')
        draft_path = Path('0192f0c1.md')
        notes_path = Path('0192f0c1.notes.md')

        node = Node(
            node_id=node_id,
            title='Chapter 1: The Beginning',
            synopsis='Opening chapter that introduces\nthe main character and setting',
            created=created_time,
            updated=updated_time,
            draft_path=draft_path,
            notes_path=notes_path,
        )

        assert node.id == node_id
        assert node.title == 'Chapter 1: The Beginning'
        assert node.synopsis == 'Opening chapter that introduces\nthe main character and setting'
        assert node.created == created_time
        assert node.updated == updated_time
        assert node.draft_path == draft_path
        assert node.notes_path == notes_path

    def test_node_id_validation(self) -> None:
        """Contract: Node must have a valid NodeId."""
        valid_node_id = NodeId('0192f0c1-2345-7123-8abc-def012345678')
        created_time = datetime.fromisoformat('2025-09-20T15:30:00+00:00')

        # Valid NodeId should work
        node = Node(
            node_id=valid_node_id,
            title=None,
            synopsis=None,
            created=created_time,
            updated=created_time,
            draft_path=Path('0192f0c1.md'),
            notes_path=Path('0192f0c1.notes.md'),
        )
        assert node.id == valid_node_id

        # None should be rejected
        with pytest.raises((TypeError, NodeValidationError)):
            Node(
                node_id=None,  # type: ignore[arg-type]
                title=None,
                synopsis=None,
                created=created_time,
                updated=created_time,
                draft_path=Path('0192f0c1.md'),
                notes_path=Path('0192f0c1.notes.md'),
            )

    def test_node_title_optional(self) -> None:
        """Contract: Node title is optional."""
        node_id = NodeId('0192f0c1-2345-7123-8abc-def012345678')
        created_time = datetime.fromisoformat('2025-09-20T15:30:00+00:00')

        # None title should be allowed
        node_without_title = Node(
            node_id=node_id,
            title=None,
            synopsis=None,
            created=created_time,
            updated=created_time,
            draft_path=Path('0192f0c1.md'),
            notes_path=Path('0192f0c1.notes.md'),
        )
        assert node_without_title.title is None

        # String title should be allowed
        node_with_title = Node(
            node_id=node_id,
            title='Chapter Title',
            synopsis=None,
            created=created_time,
            updated=created_time,
            draft_path=Path('0192f0c1.md'),
            notes_path=Path('0192f0c1.notes.md'),
        )
        assert node_with_title.title == 'Chapter Title'

    def test_node_synopsis_optional_multiline(self) -> None:
        """Contract: Node synopsis is optional and supports multi-line content."""
        node_id = NodeId('0192f0c1-2345-7123-8abc-def012345678')
        created_time = datetime.fromisoformat('2025-09-20T15:30:00+00:00')

        # None synopsis should be allowed
        node_without_synopsis = Node(
            node_id=node_id,
            title=None,
            synopsis=None,
            created=created_time,
            updated=created_time,
            draft_path=Path('0192f0c1.md'),
            notes_path=Path('0192f0c1.notes.md'),
        )
        assert node_without_synopsis.synopsis is None

        # Multi-line synopsis should be allowed
        multiline_synopsis = """Opening chapter that introduces
the main character and setting.

Key themes: identity, belonging, discovery."""

        node_with_synopsis = Node(
            node_id=node_id,
            title=None,
            synopsis=multiline_synopsis,
            created=created_time,
            updated=created_time,
            draft_path=Path('0192f0c1.md'),
            notes_path=Path('0192f0c1.notes.md'),
        )
        assert node_with_synopsis.synopsis == multiline_synopsis

    def test_node_timestamp_validation(self) -> None:
        """Contract: Node timestamps must be valid datetime objects."""
        node_id = NodeId('0192f0c1-2345-7123-8abc-def012345678')
        valid_datetime = datetime.fromisoformat('2025-09-20T15:30:00+00:00')

        # Valid datetime should work
        node = Node(
            node_id=node_id,
            title=None,
            synopsis=None,
            created=valid_datetime,
            updated=valid_datetime,
            draft_path=Path('0192f0c1.md'),
            notes_path=Path('0192f0c1.notes.md'),
        )
        assert node.created == valid_datetime
        assert node.updated == valid_datetime

        # None should be rejected
        with pytest.raises((TypeError, NodeValidationError)):
            Node(
                node_id=node_id,
                title=None,
                synopsis=None,
                created=None,  # type: ignore[arg-type]
                updated=valid_datetime,
                draft_path=Path('0192f0c1.md'),
                notes_path=Path('0192f0c1.notes.md'),
            )

    def test_node_timestamp_ordering(self) -> None:
        """Contract: Updated timestamp should be >= created timestamp."""
        node_id = NodeId('0192f0c1-2345-7123-8abc-def012345678')
        created_time = datetime.fromisoformat('2025-09-20T15:30:00+00:00')
        updated_time = datetime.fromisoformat('2025-09-20T16:45:00+00:00')

        # Updated >= created should work
        node = Node(
            node_id=node_id,
            title=None,
            synopsis=None,
            created=created_time,
            updated=updated_time,
            draft_path=Path('0192f0c1.md'),
            notes_path=Path('0192f0c1.notes.md'),
        )
        assert node.updated >= node.created

        # Same timestamps should work
        node_same_time = Node(
            node_id=node_id,
            title=None,
            synopsis=None,
            created=created_time,
            updated=created_time,
            draft_path=Path('0192f0c1.md'),
            notes_path=Path('0192f0c1.notes.md'),
        )
        assert node_same_time.updated == node_same_time.created

        # Updated < created should be rejected
        earlier_time = datetime.fromisoformat('2025-09-20T14:00:00+00:00')
        with pytest.raises(NodeValidationError):
            Node(
                node_id=node_id,
                title=None,
                synopsis=None,
                created=created_time,
                updated=earlier_time,  # Earlier than created
                draft_path=Path('0192f0c1.md'),
                notes_path=Path('0192f0c1.notes.md'),
            )

    def test_node_file_path_validation(self) -> None:
        """Contract: Node file paths must be valid Path objects."""
        node_id = NodeId('0192f0c1-2345-7123-8abc-def012345678')
        created_time = datetime.fromisoformat('2025-09-20T15:30:00+00:00')

        # Valid Path objects should work
        draft_path = Path('0192f0c1.md')
        notes_path = Path('0192f0c1.notes.md')

        node = Node(
            node_id=node_id,
            title=None,
            synopsis=None,
            created=created_time,
            updated=created_time,
            draft_path=draft_path,
            notes_path=notes_path,
        )
        assert node.draft_path == draft_path
        assert node.notes_path == notes_path

        # None should be rejected
        with pytest.raises((TypeError, NodeValidationError)):
            Node(
                node_id=node_id,
                title=None,
                synopsis=None,
                created=created_time,
                updated=created_time,
                draft_path=None,  # type: ignore[arg-type]
                notes_path=notes_path,
            )

    def test_node_path_naming_convention(self) -> None:
        """Contract: File paths should follow {id}.md and {id}.notes.md pattern."""
        node_id = NodeId('0192f0c1-2345-7123-8abc-def012345678')
        created_time = datetime.fromisoformat('2025-09-20T15:30:00+00:00')

        # Paths following the pattern should work
        expected_draft = Path('0192f0c1.md')
        expected_notes = Path('0192f0c1.notes.md')

        node = Node(
            node_id=node_id,
            title=None,
            synopsis=None,
            created=created_time,
            updated=created_time,
            draft_path=expected_draft,
            notes_path=expected_notes,
        )

        # Should be able to derive file paths from node ID
        assert node.get_expected_draft_path() == expected_draft
        assert node.get_expected_notes_path() == expected_notes

    def test_node_update_timestamp(self) -> None:
        """Contract: Node should provide method to update the updated timestamp."""
        node_id = NodeId('0192f0c1-2345-7123-8abc-def012345678')
        created_time = datetime.fromisoformat('2025-09-20T15:30:00+00:00')

        node = Node(
            node_id=node_id,
            title=None,
            synopsis=None,
            created=created_time,
            updated=created_time,
            draft_path=Path('0192f0c1.md'),
            notes_path=Path('0192f0c1.notes.md'),
        )

        original_updated = node.updated
        new_time = datetime.fromisoformat('2025-09-20T16:45:00+00:00')

        node.touch(new_time)

        assert node.updated == new_time
        assert node.updated > original_updated
        assert node.created == created_time  # Should not change

    def test_node_update_metadata(self) -> None:
        """Contract: Node should provide method to update title and synopsis."""
        node_id = NodeId('0192f0c1-2345-7123-8abc-def012345678')
        created_time = datetime.fromisoformat('2025-09-20T15:30:00+00:00')

        node = Node(
            node_id=node_id,
            title=None,
            synopsis=None,
            created=created_time,
            updated=created_time,
            draft_path=Path('0192f0c1.md'),
            notes_path=Path('0192f0c1.notes.md'),
        )

        new_title = 'Updated Chapter Title'
        new_synopsis = 'Updated synopsis content'
        update_time = datetime.fromisoformat('2025-09-20T16:45:00+00:00')

        node.update_metadata(title=new_title, synopsis=new_synopsis, updated=update_time)

        assert node.title == new_title
        assert node.synopsis == new_synopsis
        assert node.updated == update_time

    def test_node_id_immutability(self) -> None:
        """Contract: Node ID must be immutable after creation."""
        node_id = NodeId('0192f0c1-2345-7123-8abc-def012345678')
        created_time = datetime.fromisoformat('2025-09-20T15:30:00+00:00')

        node = Node(
            node_id=node_id,
            title=None,
            synopsis=None,
            created=created_time,
            updated=created_time,
            draft_path=Path('0192f0c1.md'),
            notes_path=Path('0192f0c1.notes.md'),
        )

        # Should not be able to modify the ID
        with pytest.raises(AttributeError):
            node.id = NodeId('0192f0c1-2345-7456-8abc-def012345678')  # type: ignore[misc]

    def test_node_created_timestamp_immutability(self) -> None:
        """Contract: Created timestamp must be immutable after creation."""
        node_id = NodeId('0192f0c1-2345-7123-8abc-def012345678')
        created_time = datetime.fromisoformat('2025-09-20T15:30:00+00:00')

        node = Node(
            node_id=node_id,
            title=None,
            synopsis=None,
            created=created_time,
            updated=created_time,
            draft_path=Path('0192f0c1.md'),
            notes_path=Path('0192f0c1.notes.md'),
        )

        # Should not be able to modify created timestamp directly
        with pytest.raises(AttributeError):
            node.created = datetime.fromisoformat('2025-09-20T14:00:00+00:00')  # type: ignore[misc]

    def test_node_equality_semantics(self) -> None:
        """Contract: Node equality should be based on node ID."""
        node_id = NodeId('0192f0c1-2345-7123-8abc-def012345678')
        created_time = datetime.fromisoformat('2025-09-20T15:30:00+00:00')

        node1 = Node(
            node_id=node_id,
            title='Title 1',
            synopsis=None,
            created=created_time,
            updated=created_time,
            draft_path=Path('0192f0c1.md'),
            notes_path=Path('0192f0c1.notes.md'),
        )

        node2 = Node(
            node_id=node_id,
            title='Title 2',  # Different title
            synopsis='Different synopsis',
            created=created_time,
            updated=created_time,
            draft_path=Path('0192f0c1.md'),
            notes_path=Path('0192f0c1.notes.md'),
        )

        # Same ID should make them equal despite different content
        assert node1 == node2

        # Different ID should make them different
        different_id = NodeId('0192f0c1-2345-7456-8abc-def012345678')
        node3 = Node(
            node_id=different_id,
            title='Title 1',
            synopsis=None,
            created=created_time,
            updated=created_time,
            draft_path=Path('0192f0c1-2345-7456.md'),
            notes_path=Path('0192f0c1-2345-7456.notes.md'),
        )

        assert node1 != node3

    def test_node_hashable_contract(self) -> None:
        """Contract: Node should be hashable based on node ID."""
        node_id = NodeId('0192f0c1-2345-7123-8abc-def012345678')
        created_time = datetime.fromisoformat('2025-09-20T15:30:00+00:00')

        node1 = Node(
            node_id=node_id,
            title=None,
            synopsis=None,
            created=created_time,
            updated=created_time,
            draft_path=Path('0192f0c1.md'),
            notes_path=Path('0192f0c1.notes.md'),
        )

        node2 = Node(
            node_id=node_id,
            title='Different title',
            synopsis=None,
            created=created_time,
            updated=created_time,
            draft_path=Path('0192f0c1.md'),
            notes_path=Path('0192f0c1.notes.md'),
        )

        # Same ID should have same hash
        assert hash(node1) == hash(node2)

        # Should be usable in sets
        node_set = {node1, node2}
        assert len(node_set) == 1

    def test_node_string_representation(self) -> None:
        """Contract: Node should have meaningful string representation."""
        node_id = NodeId('0192f0c1-2345-7123-8abc-def012345678')
        created_time = datetime.fromisoformat('2025-09-20T15:30:00+00:00')

        node_with_title = Node(
            node_id=node_id,
            title='Chapter 1: The Beginning',
            synopsis=None,
            created=created_time,
            updated=created_time,
            draft_path=Path('0192f0c1.md'),
            notes_path=Path('0192f0c1.notes.md'),
        )

        str_repr = str(node_with_title)
        assert 'Chapter 1: The Beginning' in str_repr

        # Node without title should show ID
        node_without_title = Node(
            node_id=node_id,
            title=None,
            synopsis=None,
            created=created_time,
            updated=created_time,
            draft_path=Path('0192f0c1.md'),
            notes_path=Path('0192f0c1.notes.md'),
        )

        str_repr_no_title = str(node_without_title)
        assert '0192f0c1' in str_repr_no_title


@pytest.fixture
def sample_node_id() -> NodeId:
    """Fixture providing a sample NodeId."""
    return NodeId('0192f0c1-2345-7123-8abc-def012345678')


@pytest.fixture
def sample_datetime() -> datetime:
    """Fixture providing a sample datetime."""
    return datetime.fromisoformat('2025-09-20T15:30:00+00:00')


@pytest.fixture
def minimal_node(sample_node_id: NodeId, sample_datetime: datetime) -> Node:
    """Fixture providing a minimal Node."""
    return Node(
        node_id=sample_node_id,
        title=None,
        synopsis=None,
        created=sample_datetime,
        updated=sample_datetime,
        draft_path=Path('0192f0c1.md'),
        notes_path=Path('0192f0c1.notes.md'),
    )


@pytest.fixture
def complete_node(sample_node_id: NodeId, sample_datetime: datetime) -> Node:
    """Fixture providing a complete Node with all fields."""
    return Node(
        node_id=sample_node_id,
        title='Chapter 1: The Beginning',
        synopsis='Opening chapter that introduces\nthe main character and setting',
        created=sample_datetime,
        updated=sample_datetime,
        draft_path=Path('0192f0c1.md'),
        notes_path=Path('0192f0c1.notes.md'),
    )
