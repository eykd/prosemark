"""Comprehensive tests for RemoveNode use case to achieve 100% coverage."""

import pytest

from prosemark.adapters.fake_console import FakeConsolePort
from prosemark.adapters.fake_logger import FakeLogger
from prosemark.adapters.fake_node_repo import FakeNodeRepo
from prosemark.adapters.fake_storage import FakeBinderRepo
from prosemark.app.remove_node import RemoveNode
from prosemark.domain.models import Binder, BinderItem, NodeId
from prosemark.exceptions import FileSystemError, NodeNotFoundError


class TestRemoveNodeCoverage:
    """Test RemoveNode use case with complete coverage."""

    @pytest.fixture
    def fake_binder_repo(self) -> FakeBinderRepo:
        """Fake BinderRepo for testing."""
        return FakeBinderRepo()

    @pytest.fixture
    def fake_node_repo(self) -> FakeNodeRepo:
        """Fake NodeRepo for testing."""
        return FakeNodeRepo()

    @pytest.fixture
    def fake_console(self) -> FakeConsolePort:
        """Fake Console for testing."""
        return FakeConsolePort()

    @pytest.fixture
    def fake_logger(self) -> FakeLogger:
        """Fake Logger for testing."""
        return FakeLogger()

    @pytest.fixture
    def remove_node(
        self,
        fake_binder_repo: FakeBinderRepo,
        fake_node_repo: FakeNodeRepo,
        fake_console: FakeConsolePort,
        fake_logger: FakeLogger,
    ) -> RemoveNode:
        """RemoveNode instance with fake dependencies."""
        return RemoveNode(
            binder_repo=fake_binder_repo,
            node_repo=fake_node_repo,
            console=fake_console,
            logger=fake_logger,
        )

    @pytest.fixture
    def binder_with_nodes(self, fake_binder_repo: FakeBinderRepo) -> Binder:
        """Binder with multiple nodes for testing."""
        child1 = BinderItem(
            display_title='Child 1', node_id=NodeId('0192f0c1-0001-7000-8000-000000000001'), children=[]
        )
        child2 = BinderItem(
            display_title='Child 2', node_id=NodeId('0192f0c1-0002-7000-8000-000000000002'), children=[]
        )
        parent = BinderItem(
            display_title='Parent', node_id=NodeId('0192f0c1-0003-7000-8000-000000000003'), children=[child1, child2]
        )
        sibling = BinderItem(
            display_title='Sibling', node_id=NodeId('0192f0c1-0004-7000-8000-000000000004'), children=[]
        )

        binder = Binder(roots=[parent, sibling])
        fake_binder_repo.save(binder)
        return binder

    def test_remove_node_without_keeping_children(
        self,
        remove_node: RemoveNode,
        fake_binder_repo: FakeBinderRepo,
        fake_console: FakeConsolePort,
        fake_logger: FakeLogger,
        binder_with_nodes: Binder,
    ) -> None:
        """Test RemoveNode removes node and its entire subtree."""
        # Arrange
        parent_id = NodeId('0192f0c1-0003-7000-8000-000000000003')

        # Act
        remove_node.execute(node_id=parent_id, keep_children=False, delete_files=False)

        # Assert - Parent and all children removed
        updated_binder = fake_binder_repo.load()
        assert len(updated_binder.roots) == 1  # Only sibling remains
        assert updated_binder.roots[0].node_id is not None
        assert updated_binder.roots[0].node_id.value == '0192f0c1-0004-7000-8000-000000000004'

        # Assert - Success messages displayed
        assert fake_console.output_contains(f'SUCCESS: Removed node {parent_id.value} from binder')
        assert fake_console.output_contains('INFO: Removed 2 child nodes')

        # Assert - Operations logged
        assert fake_logger.has_logged('info', f'Removing node: {parent_id.value}')
        assert fake_logger.has_logged('info', f'Node removed: {parent_id.value}')

    def test_remove_node_keeping_children(
        self,
        remove_node: RemoveNode,
        fake_binder_repo: FakeBinderRepo,
        fake_console: FakeConsolePort,
        binder_with_nodes: Binder,
    ) -> None:
        """Test RemoveNode removes node but promotes children to parent level."""
        # Arrange
        parent_id = NodeId('0192f0c1-0003-7000-8000-000000000003')

        # Act
        remove_node.execute(node_id=parent_id, keep_children=True, delete_files=False)

        # Assert - Parent removed but children promoted to root level
        updated_binder = fake_binder_repo.load()
        assert len(updated_binder.roots) == 3  # sibling + 2 promoted children

        # Find promoted children
        root_ids = [root.node_id.value for root in updated_binder.roots if root.node_id]
        assert '0192f0c1-0001-7000-8000-000000000001' in root_ids
        assert '0192f0c1-0002-7000-8000-000000000002' in root_ids
        assert '0192f0c1-0004-7000-8000-000000000004' in root_ids

        # Assert - Success messages displayed
        assert fake_console.output_contains(f'SUCCESS: Removed node {parent_id.value} from binder')
        assert fake_console.output_contains('INFO: Children promoted to parent level')

    def test_remove_node_with_file_deletion(
        self,
        remove_node: RemoveNode,
        fake_node_repo: FakeNodeRepo,
        fake_console: FakeConsolePort,
        binder_with_nodes: Binder,
    ) -> None:
        """Test RemoveNode deletes files when requested."""
        # Arrange
        sibling_id = NodeId('0192f0c1-0004-7000-8000-000000000004')
        # Add the node to the fake repo so it can be deleted
        fake_node_repo.create(sibling_id, 'Sibling', 'Content')

        # Act
        remove_node.execute(node_id=sibling_id, keep_children=False, delete_files=True)

        # Assert - File deletion was attempted
        assert fake_console.output_contains(f'INFO: Deleted files: {sibling_id.value}.md, {sibling_id.value}.notes.md')

    def test_remove_node_handles_file_deletion_error(
        self,
        remove_node: RemoveNode,
        fake_node_repo: FakeNodeRepo,
        fake_console: FakeConsolePort,
        binder_with_nodes: Binder,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Test RemoveNode handles file deletion errors gracefully."""
        # Arrange
        sibling_id = NodeId('0192f0c1-0004-7000-8000-000000000004')

        # Mock node_repo.delete to raise FileSystemError
        def mock_delete(node_id: 'NodeId', *, delete_files: bool) -> None:
            raise FileSystemError('Permission denied')

        monkeypatch.setattr(fake_node_repo, 'delete', mock_delete)

        # Act
        remove_node.execute(node_id=sibling_id, keep_children=False, delete_files=True)

        # Assert - Warning shown for file deletion failure
        assert fake_console.output_contains('WARNING: Could not delete files: Permission denied')

    def test_remove_node_handles_node_not_found(
        self,
        remove_node: RemoveNode,
        binder_with_nodes: Binder,
    ) -> None:
        """Test RemoveNode raises error when node to remove is not found."""
        # Arrange
        missing_id = NodeId('0192f0c1-9998-7000-8000-000000000998')

        # Act & Assert
        with pytest.raises(NodeNotFoundError) as exc_info:
            remove_node.execute(node_id=missing_id, keep_children=False, delete_files=False)

        assert f'Node {missing_id.value} not found in binder' in str(exc_info.value)

    def test_remove_node_nested_child(
        self,
        remove_node: RemoveNode,
        fake_binder_repo: FakeBinderRepo,
        fake_console: FakeConsolePort,
    ) -> None:
        """Test RemoveNode removes nested child node."""
        # Arrange - Create nested structure
        grandchild = BinderItem(
            display_title='Grandchild', node_id=NodeId('0192f0c1-0007-7000-8000-000000000007'), children=[]
        )
        child = BinderItem(
            display_title='Child', node_id=NodeId('0192f0c1-0008-7000-8000-000000000008'), children=[grandchild]
        )
        parent = BinderItem(
            display_title='Parent', node_id=NodeId('0192f0c1-0003-7000-8000-000000000003'), children=[child]
        )
        binder = Binder(roots=[parent])
        fake_binder_repo.save(binder)

        # Act - Remove deeply nested grandchild
        grandchild_id = NodeId('0192f0c1-0007-7000-8000-000000000007')
        remove_node.execute(node_id=grandchild_id, keep_children=False, delete_files=False)

        # Assert - Grandchild was found and removed
        updated_binder = fake_binder_repo.load()
        parent_item = updated_binder.roots[0]
        child_item = parent_item.children[0]
        assert len(child_item.children) == 0  # Grandchild removed

        # Assert - Success message displayed
        assert fake_console.output_contains(f'SUCCESS: Removed node {grandchild_id.value} from binder')

    def test_remove_node_leaf_node_without_children(
        self,
        remove_node: RemoveNode,
        fake_console: FakeConsolePort,
        binder_with_nodes: Binder,
    ) -> None:
        """Test RemoveNode removes leaf node (no children info message)."""
        # Arrange
        sibling_id = NodeId('0192f0c1-0004-7000-8000-000000000004')  # This node has no children

        # Act
        remove_node.execute(node_id=sibling_id, keep_children=False, delete_files=False)

        # Assert - No children-related message since node has no children
        assert fake_console.output_contains(f'SUCCESS: Removed node {sibling_id.value} from binder')
        # Should not have messages about children since sibling has none

    def test_remove_node_find_parent_and_position_recursive(
        self,
        remove_node: RemoveNode,
        fake_binder_repo: FakeBinderRepo,
    ) -> None:
        """Test _find_parent_and_position searches recursively."""
        # Arrange - Create deeply nested structure
        great_grandchild = BinderItem(
            display_title='Great Grandchild', node_id=NodeId('0192f0c1-0011-7000-8000-000000000011'), children=[]
        )
        grandchild = BinderItem(
            display_title='Grandchild',
            node_id=NodeId('0192f0c1-0007-7000-8000-000000000007'),
            children=[great_grandchild],
        )
        child = BinderItem(
            display_title='Child', node_id=NodeId('0192f0c1-0008-7000-8000-000000000008'), children=[grandchild]
        )
        parent = BinderItem(
            display_title='Parent', node_id=NodeId('0192f0c1-0003-7000-8000-000000000003'), children=[child]
        )
        binder = Binder(roots=[parent])
        fake_binder_repo.save(binder)

        # Act - Remove deeply nested great-grandchild
        great_grandchild_id = NodeId('0192f0c1-0011-7000-8000-000000000011')
        remove_node.execute(node_id=great_grandchild_id, keep_children=False, delete_files=False)

        # Assert - Great-grandchild was found and removed from deep nesting
        updated_binder = fake_binder_repo.load()
        parent_item = updated_binder.roots[0]
        child_item = parent_item.children[0]
        grandchild_item = child_item.children[0]
        assert len(grandchild_item.children) == 0  # Great-grandchild removed

    def test_remove_node_find_parent_and_position_at_root(
        self,
        remove_node: RemoveNode,
        fake_binder_repo: FakeBinderRepo,
    ) -> None:
        """Test _find_parent_and_position handles root-level nodes."""
        # Arrange
        root_node = BinderItem(
            display_title='Root Node', node_id=NodeId('0192f0c1-0015-7000-8000-000000000015'), children=[]
        )
        binder = Binder(roots=[root_node])
        fake_binder_repo.save(binder)

        # Act - Remove root-level node
        root_id = NodeId('0192f0c1-0015-7000-8000-000000000015')
        remove_node.execute(node_id=root_id, keep_children=False, delete_files=False)

        # Assert - Root node was removed
        updated_binder = fake_binder_repo.load()
        assert len(updated_binder.roots) == 0

    def test_remove_node_child_promotion_order(
        self,
        remove_node: RemoveNode,
        fake_binder_repo: FakeBinderRepo,
    ) -> None:
        """Test RemoveNode promotes children in correct order."""
        # Arrange - Create node with multiple children
        child1 = BinderItem(
            display_title='Child 1', node_id=NodeId('0192f0c1-0001-7000-8000-000000000001'), children=[]
        )
        child2 = BinderItem(
            display_title='Child 2', node_id=NodeId('0192f0c1-0002-7000-8000-000000000002'), children=[]
        )
        child3 = BinderItem(
            display_title='Child 3', node_id=NodeId('0192f0c1-0012-7000-8000-000000000012'), children=[]
        )
        parent = BinderItem(
            display_title='Parent',
            node_id=NodeId('0192f0c1-0003-7000-8000-000000000003'),
            children=[child1, child2, child3],
        )
        before_node = BinderItem(
            display_title='Before', node_id=NodeId('0192f0c1-0013-7000-8000-000000000013'), children=[]
        )
        after_node = BinderItem(
            display_title='After', node_id=NodeId('0192f0c1-0014-7000-8000-000000000014'), children=[]
        )

        binder = Binder(roots=[before_node, parent, after_node])
        fake_binder_repo.save(binder)

        # Act - Remove parent and promote children
        parent_id = NodeId('0192f0c1-0003-7000-8000-000000000003')
        remove_node.execute(node_id=parent_id, keep_children=True, delete_files=False)

        # Assert - Children promoted in order at parent's position
        updated_binder = fake_binder_repo.load()
        assert len(updated_binder.roots) == 5  # before + 3 promoted children + after

        root_ids = [root.node_id.value for root in updated_binder.roots if root.node_id]
        assert root_ids == [
            '0192f0c1-0013-7000-8000-000000000013',
            '0192f0c1-0001-7000-8000-000000000001',
            '0192f0c1-0002-7000-8000-000000000002',
            '0192f0c1-0012-7000-8000-000000000012',
            '0192f0c1-0014-7000-8000-000000000014',
        ]

    def test_remove_node_uses_current_directory_when_no_path_provided(
        self,
        remove_node: RemoveNode,
        fake_logger: FakeLogger,
        binder_with_nodes: Binder,
    ) -> None:
        """Test RemoveNode uses current directory when no project_path provided."""
        # Arrange
        sibling_id = NodeId('0192f0c1-0004-7000-8000-000000000004')

        # Act - Execute without project_path (it uses Path.cwd() internally)
        remove_node.execute(node_id=sibling_id, keep_children=False, delete_files=False, project_path=None)

        # Assert - Should complete without error (using current directory internally)
        assert fake_logger.has_logged('info', f'Removing node: {sibling_id.value}')

    def test_remove_node_dependency_injection(
        self,
        fake_binder_repo: FakeBinderRepo,
        fake_node_repo: FakeNodeRepo,
        fake_console: FakeConsolePort,
        fake_logger: FakeLogger,
    ) -> None:
        """Test RemoveNode uses all injected dependencies correctly."""
        # Arrange
        remove_node = RemoveNode(
            binder_repo=fake_binder_repo,
            node_repo=fake_node_repo,
            console=fake_console,
            logger=fake_logger,
        )

        # Verify dependencies are assigned
        assert remove_node.binder_repo is fake_binder_repo
        assert remove_node.node_repo is fake_node_repo
        assert remove_node.console is fake_console
        assert remove_node.logger is fake_logger

        # Setup and test
        node = BinderItem(
            display_title='Test Node', node_id=NodeId('0192f0c1-0009-7000-8000-000000000009'), children=[]
        )
        binder = Binder(roots=[node])
        fake_binder_repo.save(binder)

        node_id = NodeId('0192f0c1-0009-7000-8000-000000000009')
        remove_node.execute(node_id=node_id, keep_children=False, delete_files=False)

        # Assert all dependencies were used
        assert len(fake_console.get_output()) > 0
        assert fake_logger.log_count() > 0
