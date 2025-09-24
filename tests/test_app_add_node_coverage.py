"""Comprehensive tests for AddNode use case to achieve 100% coverage."""

import pytest

from prosemark.adapters.fake_clock import FakeClock
from prosemark.adapters.fake_console import FakeConsolePort
from prosemark.adapters.fake_id_generator import FakeIdGenerator
from prosemark.adapters.fake_logger import FakeLogger
from prosemark.adapters.fake_node_repo import FakeNodeRepo
from prosemark.adapters.fake_storage import FakeBinderRepo
from prosemark.app.add_node import AddNode
from prosemark.domain.models import Binder, BinderItem, NodeId


class TestAddNodeCoverage:
    """Test AddNode use case with complete coverage."""

    @pytest.fixture
    def fake_binder_repo(self) -> FakeBinderRepo:
        """Fake BinderRepo for testing."""
        return FakeBinderRepo()

    @pytest.fixture
    def fake_node_repo(self) -> FakeNodeRepo:
        """Fake NodeRepo for testing."""
        return FakeNodeRepo()

    @pytest.fixture
    def fake_id_generator(self) -> FakeIdGenerator:
        """Fake IdGenerator for testing."""
        return FakeIdGenerator()

    @pytest.fixture
    def fake_console(self) -> FakeConsolePort:
        """Fake Console for testing."""
        return FakeConsolePort()

    @pytest.fixture
    def fake_logger(self) -> FakeLogger:
        """Fake Logger for testing."""
        return FakeLogger()

    @pytest.fixture
    def fake_clock(self) -> FakeClock:
        """Fake Clock for testing."""
        return FakeClock('2025-09-14T12:00:00Z')

    @pytest.fixture
    def add_node(
        self,
        fake_binder_repo: FakeBinderRepo,
        fake_node_repo: FakeNodeRepo,
        fake_id_generator: FakeIdGenerator,
        fake_console: FakeConsolePort,
        fake_logger: FakeLogger,
        fake_clock: FakeClock,
    ) -> AddNode:
        """AddNode instance with fake dependencies."""
        return AddNode(
            binder_repo=fake_binder_repo,
            node_repo=fake_node_repo,
            id_generator=fake_id_generator,
            console=fake_console,
            logger=fake_logger,
            clock=fake_clock,
        )

    @pytest.fixture
    def empty_binder(self, fake_binder_repo: FakeBinderRepo) -> Binder:
        """Empty binder saved to repository."""
        binder = Binder(roots=[])
        fake_binder_repo.save(binder)
        return binder

    @pytest.fixture
    def binder_with_nodes(self, fake_binder_repo: FakeBinderRepo) -> Binder:
        """Binder with existing nodes for parent tests."""
        parent_id = NodeId('0192f0c1-1111-7000-8000-000000000001')
        parent_item = BinderItem(display_title='Parent Chapter', node_id=parent_id, children=[])
        binder = Binder(roots=[parent_item])
        fake_binder_repo.save(binder)
        return binder

    def test_add_node_creates_root_level_node(
        self,
        add_node: AddNode,
        fake_binder_repo: FakeBinderRepo,
        fake_node_repo: FakeNodeRepo,
        fake_id_generator: FakeIdGenerator,
        fake_console: FakeConsolePort,
        fake_logger: FakeLogger,
        empty_binder: Binder,
    ) -> None:
        """Test AddNode creates root-level node without parent specification."""
        # Arrange
        title = 'Chapter One'

        # Act
        result_id = add_node.execute(title=title, parent_id=None, position=None)

        # Assert - Node ID was generated and returned
        expected_id = NodeId('0192f0c1-0000-7000-8000-000000000001')
        assert result_id == expected_id

        # Assert - Node files were created with proper content
        assert fake_node_repo.node_exists(expected_id)

        # Assert - Node added to binder roots
        updated_binder = fake_binder_repo.load()
        assert len(updated_binder.roots) == 1
        root_item = updated_binder.roots[0]
        assert root_item.node_id == expected_id
        assert root_item.display_title == title
        assert root_item.children == []

        # Assert - Operations were logged and displayed
        assert fake_logger.has_logged('info', f'Adding node: {title}')
        assert fake_logger.has_logged('info', f'Node added: {expected_id.value}')
        assert fake_console.output_contains(f'SUCCESS: Added "{title}" ({expected_id.value})')

    def test_add_node_creates_nested_node(
        self,
        add_node: AddNode,
        fake_binder_repo: FakeBinderRepo,
        fake_node_repo: FakeNodeRepo,
        fake_console: FakeConsolePort,
        fake_logger: FakeLogger,
        binder_with_nodes: Binder,
    ) -> None:
        """Test AddNode creates nested node under specified parent."""
        # Arrange
        parent_id = NodeId('0192f0c1-1111-7000-8000-000000000001')
        title = 'Section 1.1'

        # Act
        result_id = add_node.execute(title=title, parent_id=parent_id, position=None)

        # Assert - Node was created
        expected_id = NodeId('0192f0c1-0000-7000-8000-000000000001')
        assert result_id == expected_id

        # Assert - Node files were created
        assert fake_node_repo.node_exists(expected_id)

        # Assert - Node added under parent in binder hierarchy
        updated_binder = fake_binder_repo.load()
        assert len(updated_binder.roots) == 1
        parent_item = updated_binder.roots[0]
        assert parent_item.node_id == parent_id
        assert len(parent_item.children) == 1

        child_item = parent_item.children[0]
        assert child_item.node_id == expected_id
        assert child_item.display_title == title
        assert child_item.children == []

    def test_add_node_handles_parent_not_found(
        self,
        add_node: AddNode,
        fake_console: FakeConsolePort,
        empty_binder: Binder,
    ) -> None:
        """Test AddNode handles case where parent node is not found."""
        # Arrange
        non_existent_parent = NodeId('0192f0c1-9999-7000-8000-000000000999')
        title = 'Child Node'

        # Act
        result_id = add_node.execute(title=title, parent_id=non_existent_parent, position=None)

        # Assert - Node was still created (returns the ID) but error was shown
        expected_id = NodeId('0192f0c1-0000-7000-8000-000000000001')
        assert result_id == expected_id
        assert fake_console.output_contains(f'ERROR: Parent node {non_existent_parent.value} not found')

    def test_add_node_with_specific_position_root_level(
        self,
        add_node: AddNode,
        fake_binder_repo: FakeBinderRepo,
        empty_binder: Binder,
    ) -> None:
        """Test AddNode with specific position at root level."""
        # Arrange - Add first node
        first_title = 'First Node'
        first_id = add_node.execute(title=first_title, parent_id=None, position=None)

        # Act - Add second node at position 0 (beginning)
        second_title = 'Second Node (at beginning)'
        second_id = add_node.execute(title=second_title, parent_id=None, position=0)

        # Assert - Second node was inserted at the beginning
        updated_binder = fake_binder_repo.load()
        assert len(updated_binder.roots) == 2
        assert updated_binder.roots[0].node_id == second_id
        assert updated_binder.roots[0].display_title == second_title
        assert updated_binder.roots[1].node_id == first_id
        assert updated_binder.roots[1].display_title == first_title

    def test_add_node_with_invalid_position_root_level(
        self,
        add_node: AddNode,
        fake_binder_repo: FakeBinderRepo,
        empty_binder: Binder,
    ) -> None:
        """Test AddNode with invalid position at root level defaults to append."""
        # Arrange - Add first node
        first_title = 'First Node'
        first_id = add_node.execute(title=first_title, parent_id=None, position=None)

        # Act - Add second node at invalid position (too high)
        second_title = 'Second Node (invalid position)'
        second_id = add_node.execute(title=second_title, parent_id=None, position=999)

        # Assert - Second node was appended (position ignored)
        updated_binder = fake_binder_repo.load()
        assert len(updated_binder.roots) == 2
        assert updated_binder.roots[0].node_id == first_id
        assert updated_binder.roots[1].node_id == second_id

    def test_add_node_with_specific_position_under_parent(
        self,
        add_node: AddNode,
        fake_binder_repo: FakeBinderRepo,
        binder_with_nodes: Binder,
    ) -> None:
        """Test AddNode with specific position under parent."""
        # Arrange - Add first child to parent
        parent_id = NodeId('0192f0c1-1111-7000-8000-000000000001')
        first_child_title = 'First Child'
        first_child_id = add_node.execute(title=first_child_title, parent_id=parent_id, position=None)

        # Act - Add second child at position 0 (beginning of parent's children)
        second_child_title = 'Second Child (at beginning)'
        second_child_id = add_node.execute(title=second_child_title, parent_id=parent_id, position=0)

        # Assert - Second child was inserted at the beginning of parent's children
        updated_binder = fake_binder_repo.load()
        parent_item = updated_binder.roots[0]
        assert len(parent_item.children) == 2
        assert parent_item.children[0].node_id == second_child_id
        assert parent_item.children[0].display_title == second_child_title
        assert parent_item.children[1].node_id == first_child_id
        assert parent_item.children[1].display_title == first_child_title

    def test_add_node_with_invalid_position_under_parent(
        self,
        add_node: AddNode,
        fake_binder_repo: FakeBinderRepo,
        binder_with_nodes: Binder,
    ) -> None:
        """Test AddNode with invalid position under parent defaults to append."""
        # Arrange
        parent_id = NodeId('0192f0c1-1111-7000-8000-000000000001')
        child_title = 'Child with invalid position'

        # Act - Add child at invalid position (too high)
        child_id = add_node.execute(title=child_title, parent_id=parent_id, position=999)

        # Assert - Child was appended (position ignored)
        updated_binder = fake_binder_repo.load()
        parent_item = updated_binder.roots[0]
        assert len(parent_item.children) == 1
        assert parent_item.children[0].node_id == child_id

    def test_add_node_uses_current_directory_when_no_path_provided(
        self,
        add_node: AddNode,
        fake_logger: FakeLogger,
        empty_binder: Binder,
    ) -> None:
        """Test AddNode uses current directory when no project_path provided."""
        # Arrange
        title = 'Current Dir Node'

        # Act - Execute without project_path (it uses Path.cwd() internally)
        add_node.execute(title=title, parent_id=None, position=None, project_path=None)

        # Assert - Should complete without error (using current directory internally)
        assert fake_logger.has_logged('info', f'Adding node: {title}')

    def test_add_node_find_item_recursive_search(
        self,
        add_node: AddNode,
        fake_binder_repo: FakeBinderRepo,
    ) -> None:
        """Test _find_item method searches recursively through nested items."""
        # Arrange - Create nested binder structure
        grandparent_id = NodeId('0192f0c1-1111-7000-8000-000000000001')
        parent_id = NodeId('0192f0c1-2222-7000-8000-000000000002')

        grandparent_item = BinderItem(display_title='Grandparent', node_id=grandparent_id, children=[])
        parent_item = BinderItem(display_title='Parent', node_id=parent_id, children=[])
        grandparent_item.children.append(parent_item)

        binder = Binder(roots=[grandparent_item])
        fake_binder_repo.save(binder)

        # Act - Add child under deeply nested parent
        child_title = 'Deep Child'
        add_node.execute(title=child_title, parent_id=parent_id, position=None)

        # Assert - Child was added under the correct parent
        updated_binder = fake_binder_repo.load()
        grandparent = updated_binder.roots[0]
        parent = grandparent.children[0]
        assert len(parent.children) == 1
        assert parent.children[0].display_title == child_title

    def test_add_node_find_item_returns_none_for_missing_id(
        self,
        add_node: AddNode,
        empty_binder: Binder,
    ) -> None:
        """Test _find_item returns None when item is not found."""
        # Arrange
        missing_id = NodeId('0192f0c1-9999-7000-8000-000000000999')

        # Act - This tests the _find_item method indirectly through execute
        # When parent is not found, it should show error but still return node ID
        result_id = add_node.execute(title='Test', parent_id=missing_id, position=None)

        # Assert - Method completed (would have failed if _find_item didn't handle missing items)
        assert result_id is not None

    def test_add_node_find_item_multiple_children_with_none_returns(
        self,
        add_node: AddNode,
        fake_binder_repo: FakeBinderRepo,
    ) -> None:
        """Test _find_item with multiple children where some return None (line 125->121)."""
        # Arrange - Create structure with multiple top-level items
        # where recursive search returns None for first item, then continues to second
        target_id = NodeId('0192f0c1-9999-7000-8000-000000000999')
        first_id = NodeId('0192f0c1-1111-7000-8000-000000000001')
        NodeId('0192f0c1-2222-7000-8000-000000000002')

        # Create nested structure where target is NOT in first tree
        deep_child = BinderItem(display_title='Deep Child', node_id=None, children=[])
        child1 = BinderItem(display_title='Child 1', node_id=None, children=[deep_child])
        first_root = BinderItem(display_title='First Root', node_id=first_id, children=[child1])

        # Target is in second tree
        second_root = BinderItem(display_title='Second Root', node_id=target_id, children=[])

        binder = Binder(roots=[first_root, second_root])
        fake_binder_repo.save(binder)

        # Act - Search for target_id
        # This should:
        # 1. Check first_root (first_id != target_id, no match)
        # 2. Recursively search first_root.children (returns None)
        # 3. if found: evaluates to False (since found=None)
        # 4. Continue to next iteration (line 125->121 branch)
        # 5. Check second_root (target_id == target_id, match!)
        result = add_node._find_item(binder.roots, target_id)

        # Assert
        assert result is not None
        assert result.node_id == target_id
        assert result.display_title == 'Second Root'

    def test_add_node_dependency_injection(
        self,
        fake_binder_repo: FakeBinderRepo,
        fake_node_repo: FakeNodeRepo,
        fake_id_generator: FakeIdGenerator,
        fake_console: FakeConsolePort,
        fake_logger: FakeLogger,
        fake_clock: FakeClock,
    ) -> None:
        """Test AddNode uses all injected dependencies correctly."""
        # Arrange
        add_node = AddNode(
            binder_repo=fake_binder_repo,
            node_repo=fake_node_repo,
            id_generator=fake_id_generator,
            console=fake_console,
            logger=fake_logger,
            clock=fake_clock,
        )

        # Verify dependencies are assigned
        assert add_node.binder_repo is fake_binder_repo
        assert add_node.node_repo is fake_node_repo
        assert add_node.id_generator is fake_id_generator
        assert add_node.console is fake_console
        assert add_node.logger is fake_logger
        assert add_node.clock is fake_clock

        # Setup and test
        empty_binder = Binder(roots=[])
        fake_binder_repo.save(empty_binder)

        title = 'Dependency Test'
        add_node.execute(title=title, parent_id=None, position=None)

        # Assert all dependencies were used
        assert fake_id_generator.generated_count() > 0
        assert fake_node_repo.get_node_count() > 0
        assert len(fake_console.get_output()) > 0
        assert fake_logger.log_count() > 0
