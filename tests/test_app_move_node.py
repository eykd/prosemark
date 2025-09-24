"""Tests for MoveNode use case interactor."""

import pytest

from prosemark.adapters.fake_logger import FakeLogger
from prosemark.adapters.fake_storage import FakeBinderRepo
from prosemark.app.use_cases import MoveNode
from prosemark.domain.models import Binder, BinderItem, NodeId
from prosemark.exceptions import BinderIntegrityError, NodeNotFoundError


class TestMoveNode:
    """Test MoveNode use case interactor."""

    @pytest.fixture
    def fake_binder_repo(self) -> FakeBinderRepo:
        """Fake BinderRepo for testing."""
        return FakeBinderRepo()

    @pytest.fixture
    def fake_logger(self) -> FakeLogger:
        """Fake Logger for testing."""
        return FakeLogger()

    @pytest.fixture
    def move_node(
        self,
        fake_binder_repo: FakeBinderRepo,
        fake_logger: FakeLogger,
    ) -> MoveNode:
        """MoveNode instance with fake dependencies."""
        return MoveNode(
            binder_repo=fake_binder_repo,
            logger=fake_logger,
        )

    @pytest.fixture
    def binder_with_hierarchy(self, fake_binder_repo: FakeBinderRepo) -> Binder:
        """Binder with multi-level hierarchy for testing moves."""
        # Root level nodes
        root1_id = NodeId('0192f0c1-1111-7000-8000-000000000001')
        root2_id = NodeId('0192f0c1-2222-7000-8000-000000000002')

        # Second level nodes
        child1_id = NodeId('0192f0c1-3333-7000-8000-000000000003')
        child2_id = NodeId('0192f0c1-4444-7000-8000-000000000004')

        # Third level node
        grandchild_id = NodeId('0192f0c1-5555-7000-8000-000000000005')

        # Build hierarchy: root1 -> child1 -> grandchild
        #                  root1 -> child2
        #                  root2 (no children)
        grandchild_item = BinderItem(id_=grandchild_id, display_title='Grandchild', children=[])
        child1_item = BinderItem(id_=child1_id, display_title='Child 1', children=[grandchild_item])
        child2_item = BinderItem(id_=child2_id, display_title='Child 2', children=[])
        root1_item = BinderItem(id_=root1_id, display_title='Root 1', children=[child1_item, child2_item])
        root2_item = BinderItem(id_=root2_id, display_title='Root 2', children=[])

        binder = Binder(roots=[root1_item, root2_item])
        fake_binder_repo.save(binder)
        return binder

    @pytest.fixture
    def simple_binder(self, fake_binder_repo: FakeBinderRepo) -> Binder:
        """Simple binder with two root nodes for basic tests."""
        node1_id = NodeId('0192f0c1-1111-7000-8000-000000000001')
        node2_id = NodeId('0192f0c1-2222-7000-8000-000000000002')

        item1 = BinderItem(id_=node1_id, display_title='Node 1', children=[])
        item2 = BinderItem(id_=node2_id, display_title='Node 2', children=[])

        binder = Binder(roots=[item1, item2])
        fake_binder_repo.save(binder)
        return binder

    def test_move_node_changes_parent(
        self,
        move_node: MoveNode,
        fake_binder_repo: FakeBinderRepo,
        fake_logger: FakeLogger,
        binder_with_hierarchy: Binder,
    ) -> None:
        """Test MoveNode moves node from current to new parent location."""
        # Arrange: Binder with node under parent A, target parent B exists
        source_node_id = NodeId('0192f0c1-4444-7000-8000-000000000004')  # Child 2
        target_parent_id = NodeId('0192f0c1-2222-7000-8000-000000000002')  # Root 2

        # Verify initial state
        initial_binder = fake_binder_repo.load()
        root1 = initial_binder.roots[0]  # Root 1
        root2 = initial_binder.roots[1]  # Root 2
        assert len(root1.children) == 2  # Child 1 and Child 2
        assert len(root2.children) == 0  # No children
        assert root1.children[1].id == source_node_id  # Child 2 is second child of Root 1

        # Act: Execute MoveNode to move from A to B
        move_node.execute(node_id=source_node_id, parent_id=target_parent_id, position=None)

        # Assert: Node removed from A children, added to B children
        updated_binder = fake_binder_repo.load()
        updated_root1 = updated_binder.roots[0]  # Root 1
        updated_root2 = updated_binder.roots[1]  # Root 2

        # Child 2 removed from Root 1
        assert len(updated_root1.children) == 1
        assert updated_root1.children[0].id == NodeId('0192f0c1-3333-7000-8000-000000000003')  # Only Child 1 remains

        # Child 2 added to Root 2
        assert len(updated_root2.children) == 1
        assert updated_root2.children[0].id == source_node_id
        assert updated_root2.children[0].display_title == 'Child 2'

        # Assert operations were logged
        assert fake_logger.has_logged('info', 'Starting move node operation')
        assert fake_logger.has_logged('info', 'Move node operation completed successfully')

    def test_move_node_to_root_level(
        self,
        move_node: MoveNode,
        fake_binder_repo: FakeBinderRepo,
        binder_with_hierarchy: Binder,
    ) -> None:
        """Test MoveNode moves nested node to root level with parent_id=None."""
        # Arrange: Binder with nested node under parent
        source_node_id = NodeId('0192f0c1-3333-7000-8000-000000000003')  # Child 1

        # Verify initial state
        initial_binder = fake_binder_repo.load()
        assert len(initial_binder.roots) == 2  # Root 1 and Root 2
        root1 = initial_binder.roots[0]
        assert len(root1.children) == 2  # Child 1 and Child 2

        # Act: Execute MoveNode with parent_id=None
        move_node.execute(node_id=source_node_id, parent_id=None, position=None)

        # Assert: Node removed from parent, added to binder roots
        updated_binder = fake_binder_repo.load()

        # Now 3 roots: original Root 1, Root 2, and moved Child 1
        assert len(updated_binder.roots) == 3

        # Root 1 now has only one child
        updated_root1 = updated_binder.roots[0]
        assert len(updated_root1.children) == 1
        assert updated_root1.children[0].id == NodeId('0192f0c1-4444-7000-8000-000000000004')  # Only Child 2 remains

        # Child 1 is now a root node (appended at end)
        moved_node = updated_binder.roots[2]
        assert moved_node.id == source_node_id
        assert moved_node.display_title == 'Child 1'

        # Child 1 retains its own children (grandchild)
        assert len(moved_node.children) == 1
        assert moved_node.children[0].id == NodeId('0192f0c1-5555-7000-8000-000000000005')

    def test_move_node_respects_position(
        self,
        move_node: MoveNode,
        fake_binder_repo: FakeBinderRepo,
        binder_with_hierarchy: Binder,
    ) -> None:
        """Test MoveNode inserts node at specific position in children list."""
        # Arrange: Target parent with multiple children
        source_node_id = NodeId('0192f0c1-5555-7000-8000-000000000005')  # Grandchild
        target_parent_id = NodeId('0192f0c1-1111-7000-8000-000000000001')  # Root 1

        # Verify initial state: Root 1 has 2 children
        initial_binder = fake_binder_repo.load()
        root1 = initial_binder.roots[0]
        assert len(root1.children) == 2

        # Act: Execute MoveNode with specific position index (position 1 = between existing children)
        move_node.execute(node_id=source_node_id, parent_id=target_parent_id, position=1)

        # Assert: Node inserted at exact position in children list
        updated_binder = fake_binder_repo.load()
        updated_root1 = updated_binder.roots[0]

        # Root 1 now has 3 children
        assert len(updated_root1.children) == 3

        # Children are in order: Child 1, Grandchild (moved), Child 2
        assert updated_root1.children[0].id == NodeId('0192f0c1-3333-7000-8000-000000000003')  # Child 1
        assert updated_root1.children[1].id == source_node_id  # Grandchild (moved to position 1)
        assert updated_root1.children[2].id == NodeId('0192f0c1-4444-7000-8000-000000000004')  # Child 2

        # Original parent (Child 1) no longer has grandchild
        child1 = updated_root1.children[0]
        assert len(child1.children) == 0

    def test_move_node_position_out_of_bounds_appends(
        self,
        move_node: MoveNode,
        fake_binder_repo: FakeBinderRepo,
        simple_binder: Binder,
    ) -> None:
        """Test MoveNode appends when position is out of bounds."""
        # Arrange
        source_node_id = NodeId('0192f0c1-1111-7000-8000-000000000001')  # Node 1
        target_parent_id = NodeId('0192f0c1-2222-7000-8000-000000000002')  # Node 2 (will become parent)

        # Act: Use position 999 (way out of bounds)
        move_node.execute(node_id=source_node_id, parent_id=target_parent_id, position=999)

        # Assert: Node was appended (position effectively ignored)
        updated_binder = fake_binder_repo.load()

        # Only one root remains (Node 2)
        assert len(updated_binder.roots) == 1
        root = updated_binder.roots[0]
        assert root.id == target_parent_id

        # Node 1 was added as child (appended since position was out of bounds)
        assert len(root.children) == 1
        assert root.children[0].id == source_node_id

    def test_move_node_prevents_circular_dependency(
        self,
        move_node: MoveNode,
        fake_logger: FakeLogger,
        binder_with_hierarchy: Binder,
    ) -> None:
        """Test MoveNode prevents circular dependencies by checking ancestors."""
        # Arrange: Parent node with child, attempt to move parent under child
        parent_node_id = NodeId('0192f0c1-1111-7000-8000-000000000001')  # Root 1
        child_node_id = NodeId('0192f0c1-3333-7000-8000-000000000003')  # Child 1

        # Act & Assert: Execute MoveNode creating circular reference
        with pytest.raises(BinderIntegrityError) as exc_info:
            move_node.execute(node_id=parent_node_id, parent_id=child_node_id, position=None)

        # Assert proper error message and context
        assert 'Move would create circular dependency' in str(exc_info.value)
        assert str(parent_node_id) in str(exc_info.value)
        assert str(child_node_id) in str(exc_info.value)

        # Assert error was logged
        assert fake_logger.has_logged('error', 'Circular dependency detected')

    def test_move_node_prevents_deep_circular_dependency(
        self,
        move_node: MoveNode,
        binder_with_hierarchy: Binder,
    ) -> None:
        """Test MoveNode prevents deep circular dependencies (grandparent under grandchild)."""
        # Arrange: Try to move Root 1 under its grandchild
        root_node_id = NodeId('0192f0c1-1111-7000-8000-000000000001')  # Root 1
        grandchild_node_id = NodeId('0192f0c1-5555-7000-8000-000000000005')  # Grandchild

        # Act & Assert: This should be prevented (Root 1 -> Child 1 -> Grandchild hierarchy)
        with pytest.raises(BinderIntegrityError) as exc_info:
            move_node.execute(node_id=root_node_id, parent_id=grandchild_node_id, position=None)

        assert 'Move would create circular dependency' in str(exc_info.value)

    def test_move_node_allows_move_to_sibling(
        self,
        move_node: MoveNode,
        fake_binder_repo: FakeBinderRepo,
        binder_with_hierarchy: Binder,
    ) -> None:
        """Test MoveNode allows moving to sibling (no circular dependency)."""
        # Arrange: Move Child 2 under Child 1 (siblings)
        source_node_id = NodeId('0192f0c1-4444-7000-8000-000000000004')  # Child 2
        target_parent_id = NodeId('0192f0c1-3333-7000-8000-000000000003')  # Child 1

        # Act: This should be allowed
        move_node.execute(node_id=source_node_id, parent_id=target_parent_id, position=None)

        # Assert: Move succeeded
        updated_binder = fake_binder_repo.load()
        root1 = updated_binder.roots[0]

        # Root 1 now has only 1 child (Child 1)
        assert len(root1.children) == 1
        child1 = root1.children[0]

        # Child 1 now has 2 children (original Grandchild + moved Child 2)
        assert len(child1.children) == 2
        assert child1.children[1].id == source_node_id  # Child 2 appended

    def test_move_node_validates_source_node_exists(
        self,
        move_node: MoveNode,
        fake_logger: FakeLogger,
        simple_binder: Binder,
    ) -> None:
        """Test MoveNode validates source node exists in binder."""
        # Arrange
        non_existent_node_id = NodeId('0192f0c1-9999-7000-8000-000000000999')
        target_parent_id = NodeId('0192f0c1-2222-7000-8000-000000000002')  # Node 2

        # Act & Assert: Execute MoveNode with non-existent source
        with pytest.raises(NodeNotFoundError) as exc_info:
            move_node.execute(node_id=non_existent_node_id, parent_id=target_parent_id, position=None)

        # Assert proper error message and context
        assert 'Source node not found in binder' in str(exc_info.value)
        assert str(non_existent_node_id) in str(exc_info.value)

        # Assert error was logged
        assert fake_logger.has_logged('error', 'Source node not found in binder')

    def test_move_node_validates_target_parent_exists(
        self,
        move_node: MoveNode,
        fake_logger: FakeLogger,
        simple_binder: Binder,
    ) -> None:
        """Test MoveNode validates target parent exists when specified."""
        # Arrange
        source_node_id = NodeId('0192f0c1-1111-7000-8000-000000000001')  # Node 1
        non_existent_parent_id = NodeId('0192f0c1-9999-7000-8000-000000000999')

        # Act & Assert: Execute MoveNode with non-existent target parent
        with pytest.raises(NodeNotFoundError) as exc_info:
            move_node.execute(node_id=source_node_id, parent_id=non_existent_parent_id, position=None)

        # Assert proper error message and context
        assert 'Target parent not found in binder' in str(exc_info.value)
        assert str(non_existent_parent_id) in str(exc_info.value)

        # Assert error was logged
        assert fake_logger.has_logged('error', 'Target parent not found in binder')

    def test_move_node_maintains_node_subtree(
        self,
        move_node: MoveNode,
        fake_binder_repo: FakeBinderRepo,
        binder_with_hierarchy: Binder,
    ) -> None:
        """Test MoveNode moves entire subtree intact."""
        # Arrange: Move Child 1 (which has Grandchild) to Root 2
        source_node_id = NodeId('0192f0c1-3333-7000-8000-000000000003')  # Child 1
        target_parent_id = NodeId('0192f0c1-2222-7000-8000-000000000002')  # Root 2
        grandchild_id = NodeId('0192f0c1-5555-7000-8000-000000000005')  # Grandchild

        # Act
        move_node.execute(node_id=source_node_id, parent_id=target_parent_id, position=None)

        # Assert: Child 1 and its subtree moved intact
        updated_binder = fake_binder_repo.load()
        root2 = updated_binder.roots[1]

        # Root 2 now has Child 1 as a child
        assert len(root2.children) == 1
        moved_child1 = root2.children[0]
        assert moved_child1.id == source_node_id

        # Child 1 still has its original child (Grandchild)
        assert len(moved_child1.children) == 1
        assert moved_child1.children[0].id == grandchild_id

    def test_move_node_position_zero_prepends(
        self,
        move_node: MoveNode,
        fake_binder_repo: FakeBinderRepo,
        binder_with_hierarchy: Binder,
    ) -> None:
        """Test MoveNode position 0 prepends to beginning of children."""
        # Arrange: Move Child 2 to position 0 under Root 2
        source_node_id = NodeId('0192f0c1-4444-7000-8000-000000000004')  # Child 2
        target_parent_id = NodeId('0192f0c1-2222-7000-8000-000000000002')  # Root 2

        # First add another child to Root 2 so we can test prepending
        another_child_id = NodeId('0192f0c1-6666-7000-8000-000000000006')
        another_child = BinderItem(id_=another_child_id, display_title='Another Child', children=[])
        initial_binder = fake_binder_repo.load()
        initial_binder.roots[1].children.append(another_child)
        fake_binder_repo.save(initial_binder)

        # Act: Move to position 0
        move_node.execute(node_id=source_node_id, parent_id=target_parent_id, position=0)

        # Assert: Node was prepended (position 0)
        updated_binder = fake_binder_repo.load()
        root2 = updated_binder.roots[1]

        assert len(root2.children) == 2
        assert root2.children[0].id == source_node_id  # Child 2 at position 0
        assert root2.children[1].id == another_child_id  # Another Child moved to position 1

    def test_move_node_logs_operations(
        self,
        move_node: MoveNode,
        fake_logger: FakeLogger,
        simple_binder: Binder,
    ) -> None:
        """Test MoveNode logs all operations with source and destination details."""
        # Arrange
        source_node_id = NodeId('0192f0c1-1111-7000-8000-000000000001')
        target_parent_id = NodeId('0192f0c1-2222-7000-8000-000000000002')

        # Act
        move_node.execute(node_id=source_node_id, parent_id=target_parent_id, position=None)

        # Assert: Operations were logged with source and destination details
        assert fake_logger.has_logged('info', 'Starting move node operation')
        assert fake_logger.has_logged('debug', 'Validating source and target nodes')
        assert fake_logger.has_logged('debug', 'Checking for circular dependencies')
        assert fake_logger.has_logged('debug', 'Removing node from current location')
        assert fake_logger.has_logged('debug', 'Adding node to new location')
        assert fake_logger.has_logged('info', 'Move node operation completed successfully')

        # Verify NodeIds appear in log context
        logs = fake_logger.get_logs()
        log_text = str(logs)
        assert str(source_node_id) in log_text
        assert str(target_parent_id) in log_text

    def test_move_node_uses_injected_dependencies(
        self,
        fake_binder_repo: FakeBinderRepo,
        fake_logger: FakeLogger,
    ) -> None:
        """Test MoveNode uses all injected dependencies correctly."""
        # Arrange
        move_node_interactor = MoveNode(
            binder_repo=fake_binder_repo,
            logger=fake_logger,
        )

        # Create simple test data
        node1_id = NodeId('0192f0c1-1111-7000-8000-000000000001')
        node2_id = NodeId('0192f0c1-2222-7000-8000-000000000002')
        item1 = BinderItem(id_=node1_id, display_title='Node 1', children=[])
        item2 = BinderItem(id_=node2_id, display_title='Node 2', children=[])
        binder = Binder(roots=[item1, item2])
        fake_binder_repo.save(binder)

        # Act
        move_node_interactor.execute(node_id=node1_id, parent_id=node2_id, position=None)

        # Assert all dependencies were used
        # BinderRepo was used to load and save
        updated_binder = fake_binder_repo.load()
        assert len(updated_binder.roots) == 1  # Node 1 moved under Node 2

        # Logger recorded operations
        assert fake_logger.log_count() > 0
        assert fake_logger.has_logged('info', 'Starting move node operation')

    def test_move_node_move_to_same_parent_different_position(
        self,
        move_node: MoveNode,
        fake_binder_repo: FakeBinderRepo,
        binder_with_hierarchy: Binder,
    ) -> None:
        """Test MoveNode can reorder children within same parent."""
        # Arrange: Move Child 2 to position 0 within Root 1 (same parent, different position)
        source_node_id = NodeId('0192f0c1-4444-7000-8000-000000000004')  # Child 2
        target_parent_id = NodeId('0192f0c1-1111-7000-8000-000000000001')  # Root 1 (current parent)

        # Verify initial order: Child 1, Child 2
        initial_binder = fake_binder_repo.load()
        root1 = initial_binder.roots[0]
        assert root1.children[0].id == NodeId('0192f0c1-3333-7000-8000-000000000003')  # Child 1
        assert root1.children[1].id == source_node_id  # Child 2

        # Act: Move Child 2 to position 0 within same parent
        move_node.execute(node_id=source_node_id, parent_id=target_parent_id, position=0)

        # Assert: Order changed to Child 2, Child 1
        updated_binder = fake_binder_repo.load()
        updated_root1 = updated_binder.roots[0]
        assert len(updated_root1.children) == 2  # Same number of children
        assert updated_root1.children[0].id == source_node_id  # Child 2 now first
        assert updated_root1.children[1].id == NodeId('0192f0c1-3333-7000-8000-000000000003')  # Child 1 now second

    def test_move_node_self_move_is_noop(
        self,
        move_node: MoveNode,
        fake_binder_repo: FakeBinderRepo,
        fake_logger: FakeLogger,
        simple_binder: Binder,
    ) -> None:
        """Test MoveNode handles self-move (node to its current parent at same position) gracefully."""
        # Arrange: Try to move Node 1 to its current location (root level, same position)
        source_node_id = NodeId('0192f0c1-1111-7000-8000-000000000001')  # Node 1

        # Capture initial state
        initial_binder = fake_binder_repo.load()
        initial_structure = str(initial_binder.roots)

        # Act: Move to same location (root level, position 0)
        move_node.execute(node_id=source_node_id, parent_id=None, position=0)

        # Assert: Structure unchanged (move was essentially a no-op)
        updated_binder = fake_binder_repo.load()
        assert str(updated_binder.roots) == initial_structure

        # Assert: Operation was still logged (algorithm executed but result was same)
        assert fake_logger.has_logged('info', 'Move node operation completed successfully')

    def test_move_node_handles_empty_binder(
        self,
        move_node: MoveNode,
        fake_binder_repo: FakeBinderRepo,
    ) -> None:
        """Test MoveNode handles operations on empty binder gracefully."""
        # Arrange: Empty binder
        empty_binder = Binder(roots=[])
        fake_binder_repo.save(empty_binder)

        non_existent_node_id = NodeId('0192f0c1-1111-7000-8000-000000000001')

        # Act & Assert: Should raise NodeNotFoundError for empty binder
        with pytest.raises(NodeNotFoundError) as exc_info:
            move_node.execute(node_id=non_existent_node_id, parent_id=None, position=None)

        assert 'Source node not found in binder' in str(exc_info.value)

    def test_move_node_handles_item_without_id(
        self,
        move_node: MoveNode,
        fake_binder_repo: FakeBinderRepo,
    ) -> None:
        """Test MoveNode handles BinderItem without NodeId gracefully."""
        # Arrange: Create a binder item without NodeId (defensive programming test)
        item_without_id = BinderItem(id_=None, display_title='No ID Item', children=[])
        binder = Binder(roots=[item_without_id])
        fake_binder_repo.save(binder)

        # Act & Assert: This is a defensive case that shouldn't happen in normal operation
        # but tests the error handling for malformed data
        with pytest.raises(BinderIntegrityError) as exc_info:
            move_node._remove_node_from_current_location(binder, item_without_id)

        assert 'Cannot remove item without NodeId' in str(exc_info.value)

    def test_move_node_handles_missing_parent_in_add_location(
        self,
        move_node: MoveNode,
        fake_binder_repo: FakeBinderRepo,
        simple_binder: Binder,
    ) -> None:
        """Test MoveNode handles case where parent is removed during operation."""
        # Arrange: Create a source item and a phantom parent ID
        source_node_id = NodeId('0192f0c1-1111-7000-8000-000000000001')  # Node 1
        phantom_parent_id = NodeId('0192f0c1-9999-7000-8000-000000000999')

        binder = fake_binder_repo.load()
        source_item = binder.find_by_id(source_node_id)
        assert source_item is not None  # Ensure we found the item for type checking

        # Act & Assert: This tests the defensive check in _add_node_to_new_location
        with pytest.raises(NodeNotFoundError) as exc_info:
            move_node._add_node_to_new_location(binder, source_item, phantom_parent_id, None)

        assert 'Parent item not found' in str(exc_info.value)

    def test_move_node_handles_negative_position(
        self,
        move_node: MoveNode,
        fake_binder_repo: FakeBinderRepo,
        simple_binder: Binder,
    ) -> None:
        """Test MoveNode handles negative position by treating as 0."""
        # Arrange
        source_node_id = NodeId('0192f0c1-1111-7000-8000-000000000001')  # Node 1
        target_parent_id = NodeId('0192f0c1-2222-7000-8000-000000000002')  # Node 2

        # Act: Use negative position
        move_node.execute(node_id=source_node_id, parent_id=target_parent_id, position=-5)

        # Assert: Node was inserted at position 0 (negative treated as 0)
        updated_binder = fake_binder_repo.load()
        target_parent = updated_binder.roots[0]  # Node 2 becomes only root
        assert len(target_parent.children) == 1
        assert target_parent.children[0].id == source_node_id

    def test_move_node_ancestor_traversal_edge_case(
        self,
        move_node: MoveNode,
        fake_binder_repo: FakeBinderRepo,
    ) -> None:
        """Test ancestor traversal when node has no parent found (edge case)."""
        # Arrange: Create a scenario where ancestor traversal reaches root
        root_id = NodeId('0192f0c1-1111-7000-8000-000000000001')
        child_id = NodeId('0192f0c1-2222-7000-8000-000000000002')
        orphan_id = NodeId('0192f0c1-3333-7000-8000-000000000003')

        child_item = BinderItem(id_=child_id, display_title='Child', children=[])
        root_item = BinderItem(id_=root_id, display_title='Root', children=[child_item])
        orphan_item = BinderItem(id_=orphan_id, display_title='Orphan', children=[])

        binder = Binder(roots=[root_item, orphan_item])
        fake_binder_repo.save(binder)

        # Act: Test ancestor check between unrelated nodes (should return False)
        result = move_node._is_ancestor(binder, orphan_id, child_id)

        # Assert: Orphan is not an ancestor of child
        assert result is False
