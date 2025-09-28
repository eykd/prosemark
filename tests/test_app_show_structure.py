"""Tests for ShowStructure use case interactor."""

import pytest

from prosemark.adapters.fake_logger import FakeLogger
from prosemark.adapters.fake_storage import FakeBinderRepo
from prosemark.app.use_cases import ShowStructure
from prosemark.domain.models import Binder, BinderItem, NodeId
from prosemark.exceptions import NodeNotFoundError


class TestShowStructure:
    """Test ShowStructure use case interactor."""

    @pytest.fixture
    def fake_binder_repo(self) -> FakeBinderRepo:
        """Fake BinderRepo for testing."""
        return FakeBinderRepo()

    @pytest.fixture
    def fake_logger(self) -> FakeLogger:
        """Fake Logger for testing."""
        return FakeLogger()

    @pytest.fixture
    def show_structure(
        self,
        fake_binder_repo: FakeBinderRepo,
        fake_logger: FakeLogger,
    ) -> ShowStructure:
        """ShowStructure instance with fake dependencies."""
        return ShowStructure(
            binder_repo=fake_binder_repo,
            logger=fake_logger,
        )

    @pytest.fixture
    def empty_binder(self, fake_binder_repo: FakeBinderRepo) -> Binder:
        """Empty binder saved to repository."""
        binder = Binder(roots=[])
        fake_binder_repo.save(binder)
        return binder

    @pytest.fixture
    def complex_binder(self, fake_binder_repo: FakeBinderRepo) -> Binder:
        """Complex binder with multiple levels of hierarchy."""
        # Create nodes with IDs
        part1_id = NodeId('0192f0c1-1111-7000-8000-000000000001')
        chapter1_id = NodeId('0192f0c1-2222-7000-8000-000000000002')
        section1_id = NodeId('0192f0c1-3333-7000-8000-000000000003')
        chapter2_id = NodeId('0192f0c1-4444-7000-8000-000000000004')
        part2_id = NodeId('0192f0c1-5555-7000-8000-000000000005')

        # Create hierarchy: Part 1 > Chapter 1 > Section 1, Chapter 2; Part 2
        section1_item = BinderItem(id_=section1_id, display_title='Section 1.1', children=[])
        chapter1_item = BinderItem(id_=chapter1_id, display_title='Chapter 1', children=[section1_item])
        chapter2_item = BinderItem(id_=chapter2_id, display_title='Chapter 2', children=[])
        part1_item = BinderItem(id_=part1_id, display_title='Part 1', children=[chapter1_item, chapter2_item])
        part2_item = BinderItem(id_=part2_id, display_title='Part 2', children=[])

        binder = Binder(roots=[part1_item, part2_item])
        fake_binder_repo.save(binder)
        return binder

    @pytest.fixture
    def binder_with_placeholders(self, fake_binder_repo: FakeBinderRepo) -> Binder:
        """Binder containing placeholder items (no ID)."""
        # Create mix of real nodes and placeholders
        real_node_id = NodeId('0192f0c1-1111-7000-8000-000000000001')
        real_item = BinderItem(id_=real_node_id, display_title='Real Chapter', children=[])
        placeholder_item = BinderItem(id_=None, display_title='Placeholder Section', children=[])

        binder = Binder(roots=[real_item, placeholder_item])
        fake_binder_repo.save(binder)
        return binder

    def test_full_binder_structure_display(
        self,
        show_structure: ShowStructure,
        fake_logger: FakeLogger,
        complex_binder: Binder,
    ) -> None:
        """Test full binder structure display.

        Given: A binder with multiple levels of hierarchy
        When: ShowStructure is called without node filter
        Then: Returns complete tree representation
        """
        # Act
        result = show_structure.execute()

        # Assert - Complete tree structure is displayed
        lines = result.strip().split('\n')

        # Should show all nodes in tree format with IDs
        assert 'Part 1 (0192f0c1-1111-7000-8000-000000000001)' in result
        assert 'Part 2 (0192f0c1-5555-7000-8000-000000000005)' in result
        assert 'Chapter 1 (0192f0c1-2222-7000-8000-000000000002)' in result
        assert 'Chapter 2 (0192f0c1-4444-7000-8000-000000000004)' in result
        assert 'Section 1.1 (0192f0c1-3333-7000-8000-000000000003)' in result

        # Check hierarchical formatting with tree characters
        assert any('├─' in line or '└─' in line for line in lines)
        assert any('│' in line for line in lines)  # Should have vertical connectors

        # Assert - Operation was logged
        assert fake_logger.has_logged('info', 'Displaying full binder structure')
        assert fake_logger.has_logged('debug', 'Found 5 total items in binder'), 'Debug log message not found'

    def test_subtree_structure_display(
        self,
        show_structure: ShowStructure,
        fake_logger: FakeLogger,
        complex_binder: Binder,
    ) -> None:
        """Test subtree structure display.

        Given: A binder with nested structure
        When: ShowStructure is called with specific node_id
        Then: Returns subtree starting from that node
        """
        # Arrange
        part1_id = NodeId('0192f0c1-1111-7000-8000-000000000001')

        # Act
        result = show_structure.execute(node_id=part1_id)

        # Assert - Only subtree from Part 1 is shown with IDs
        assert 'Part 1 (0192f0c1-1111-7000-8000-000000000001)' in result
        assert 'Chapter 1 (0192f0c1-2222-7000-8000-000000000002)' in result
        assert 'Chapter 2 (0192f0c1-4444-7000-8000-000000000004)' in result
        assert 'Section 1.1 (0192f0c1-3333-7000-8000-000000000003)' in result

        # Part 2 should NOT appear in subtree
        assert 'Part 2' not in result

        # Should still have hierarchical formatting
        lines = result.strip().split('\n')
        assert any('├─' in line or '└─' in line for line in lines)

        # Assert - Subtree operation was logged
        assert fake_logger.has_logged('info', 'Displaying subtree structure')
        assert fake_logger.has_logged('debug', 'Found subtree root')

    def test_empty_binder_handling(
        self,
        show_structure: ShowStructure,
        fake_logger: FakeLogger,
        empty_binder: Binder,
    ) -> None:
        """Test empty binder handling.

        Given: An empty binder with no nodes
        When: ShowStructure is called
        Then: Returns appropriate empty structure message
        """
        # Act
        result = show_structure.execute()

        # Assert - Appropriate empty message
        expected_message = 'Binder is empty - no nodes to display'
        assert result == expected_message

        # Assert - Empty binder was logged
        assert fake_logger.has_logged('info', 'Displaying full binder structure')
        assert fake_logger.has_logged('debug', 'Binder is empty')

    def test_placeholders_in_structure(
        self,
        show_structure: ShowStructure,
        fake_logger: FakeLogger,
        binder_with_placeholders: Binder,
    ) -> None:
        """Test placeholders in structure.

        Given: A binder containing placeholder items (no ID)
        When: ShowStructure is called
        Then: Displays placeholders with distinctive formatting
        """
        # Act
        result = show_structure.execute()

        # Assert - Both real and placeholder items shown
        assert 'Real Chapter (0192f0c1-1111-7000-8000-000000000001)' in result
        assert 'Placeholder Section [Placeholder]' in result

        # Assert - Real node shows ID, not placeholder marker
        real_line = next(line for line in result.split('\n') if 'Real Chapter' in line)
        assert '0192f0c1-1111-7000-8000-000000000001' in real_line
        assert '[Placeholder]' not in real_line

        # Placeholder line should have marker, not ID
        placeholder_line = next(line for line in result.split('\n') if 'Placeholder Section' in line)
        assert '[Placeholder]' in placeholder_line
        assert '0192f0c1' not in placeholder_line  # Should not have any UUID

        # Assert - Mixed content was logged
        assert fake_logger.has_logged('debug', 'Found 1 placeholders in structure')

    def test_node_not_found_for_subtree(
        self,
        show_structure: ShowStructure,
        fake_logger: FakeLogger,
        complex_binder: Binder,
    ) -> None:
        """Test node not found for subtree.

        Given: A request for subtree from non-existent node
        When: ShowStructure is called with invalid node_id
        Then: Raises NodeNotFoundError
        """
        # Arrange
        invalid_node_id = NodeId('0192f0c1-9999-7000-8000-000000000999')

        # Act & Assert
        with pytest.raises(NodeNotFoundError) as exc_info:
            show_structure.execute(node_id=invalid_node_id)

        assert 'Node not found for subtree display' in str(exc_info.value)
        assert str(invalid_node_id) in str(exc_info.value)

        # Assert - Error was logged
        assert fake_logger.has_logged('error', 'Node not found for subtree display')

    def test_structure_with_orphaned_nodes(
        self,
        show_structure: ShowStructure,
        fake_logger: FakeLogger,
        fake_binder_repo: FakeBinderRepo,
    ) -> None:
        """Test structure with orphaned nodes.

        Given: Nodes exist but aren't in binder structure
        When: ShowStructure is called
        Then: Shows binder structure (orphans handled by audit)

        Note: This tests that ShowStructure only displays what's in the binder,
        not orphaned nodes that might exist in the filesystem.
        """
        # Arrange - Create binder with only some nodes in structure
        included_id = NodeId('0192f0c1-1111-7000-8000-000000000001')
        included_item = BinderItem(id_=included_id, display_title='Included Node', children=[])

        # Note: We don't actually create orphaned nodes in the filesystem
        # since ShowStructure only reads from the binder structure
        binder = Binder(roots=[included_item])
        fake_binder_repo.save(binder)

        # Act
        result = show_structure.execute()

        # Assert - Only binder structure nodes are shown
        assert 'Included Node' in result

        # Structure should be clean and only show what's in binder
        lines = [line.strip() for line in result.split('\n') if line.strip()]
        assert len(lines) == 1  # Only one node in structure

        # Assert - Normal structure display logged
        assert fake_logger.has_logged('info', 'Displaying full binder structure')

    def test_structure_formatting_uses_tree_characters(
        self,
        show_structure: ShowStructure,
        complex_binder: Binder,
    ) -> None:
        """Test structure formatting uses proper tree characters."""
        # Act
        result = show_structure.execute()

        # Assert - Uses proper tree drawing characters
        assert '├─' in result  # Branch connector
        assert '└─' in result  # Last branch connector
        assert '│' in result  # Vertical connector

        # Should have proper indentation structure
        lines = result.split('\n')
        root_lines = [line for line in lines if not line.startswith(' ') and line.strip()]
        assert len(root_lines) >= 2  # Should have multiple root items

    def test_structure_includes_node_titles_and_display_names(
        self,
        show_structure: ShowStructure,
        complex_binder: Binder,
    ) -> None:
        """Test structure includes node titles and display names in output."""
        # Act
        result = show_structure.execute()

        # Assert - All display titles are present
        assert 'Part 1' in result
        assert 'Part 2' in result
        assert 'Chapter 1' in result
        assert 'Chapter 2' in result
        assert 'Section 1.1' in result

    def test_execute_with_none_node_id_shows_full_structure(
        self,
        show_structure: ShowStructure,
        complex_binder: Binder,
    ) -> None:
        """Test execute with None node_id shows full structure."""
        # Act
        result = show_structure.execute(node_id=None)

        # Assert - Shows full structure (same as no parameter)
        assert 'Part 1' in result
        assert 'Part 2' in result

        # Should show all 5 nodes
        node_count = result.count('├─') + result.count('└─')
        assert node_count == 5

    def test_logging_captures_operation_details(
        self,
        show_structure: ShowStructure,
        fake_logger: FakeLogger,
        complex_binder: Binder,
    ) -> None:
        """Test logging captures all operation details."""
        # Arrange
        part1_id = NodeId('0192f0c1-1111-7000-8000-000000000001')

        # Act - Full structure
        show_structure.execute()

        # Act - Subtree
        show_structure.execute(node_id=part1_id)

        # Assert - Both operations logged with appropriate details
        logs = fake_logger.get_logs()

        # Should have logs for both full and subtree operations
        info_logs = [log for log in logs if log[0] == 'info']
        assert len(info_logs) >= 2

        # Should log structure completion
        assert any('Structure display completed' in str(log) for log in logs)

    def test_format_items_with_empty_list(
        self,
        show_structure: ShowStructure,
    ) -> None:
        """Test _format_items with empty list returns empty string.

        This tests the edge case at line 1163 where an empty items list is passed.
        """
        # Act - Call internal method with empty list
        result = show_structure._format_items([], '')

        # Assert - Should return empty string
        assert result == ''

    def test_format_items_with_root_connectors_empty_list(
        self,
        show_structure: ShowStructure,
    ) -> None:
        """Test _format_items_with_root_connectors with empty list returns empty string.

        This tests the edge case at line 1184 where an empty items list is passed.
        """
        # Act - Call internal method with empty list
        result = show_structure._format_items_with_root_connectors([])

        # Assert - Should return empty string
        assert result == ''
