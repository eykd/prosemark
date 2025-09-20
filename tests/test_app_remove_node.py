"""Tests for RemoveNode use case interactor."""

import pytest

from prosemark.adapters.fake_logger import FakeLogger
from prosemark.adapters.fake_node_repo import FakeNodeRepo
from prosemark.adapters.fake_storage import FakeBinderRepo
from prosemark.app.use_cases import RemoveNode
from prosemark.domain.models import Binder, BinderItem, NodeId
from prosemark.exceptions import NodeNotFoundError


class TestRemoveNode:
    """Test RemoveNode use case interactor."""

    @pytest.fixture
    def fake_binder_repo(self) -> FakeBinderRepo:
        """Fake BinderRepo for testing."""
        return FakeBinderRepo()

    @pytest.fixture
    def fake_node_repo(self) -> FakeNodeRepo:
        """Fake NodeRepo for testing."""
        return FakeNodeRepo()

    @pytest.fixture
    def fake_logger(self) -> FakeLogger:
        """Fake Logger for testing."""
        return FakeLogger()

    @pytest.fixture
    def remove_node(
        self,
        fake_binder_repo: FakeBinderRepo,
        fake_node_repo: FakeNodeRepo,
        fake_logger: FakeLogger,
    ) -> RemoveNode:
        """RemoveNode interactor with fake dependencies."""
        return RemoveNode(
            binder_repo=fake_binder_repo,
            node_repo=fake_node_repo,
            logger=fake_logger,
        )

    def test_remove_node_preserves_files(
        self,
        remove_node: RemoveNode,
        fake_binder_repo: FakeBinderRepo,
        fake_node_repo: FakeNodeRepo,
    ) -> None:
        """Test removing node from binder while preserving files."""
        # Arrange: Binder with node, delete_files=False
        node_id = NodeId.generate()
        binder = Binder(roots=[BinderItem(id_=node_id, display_title='Test Node', children=[])])
        fake_binder_repo.save(binder)

        # Act: Execute RemoveNode preserving files
        remove_node.execute(node_id, delete_files=False)

        # Assert: Node removed from binder, files remain on disk
        updated_binder = fake_binder_repo.load()
        assert len(updated_binder.roots) == 0
        assert not fake_node_repo.delete_called_with(node_id, delete_files=False)

    def test_remove_node_deletes_files(
        self,
        remove_node: RemoveNode,
        fake_binder_repo: FakeBinderRepo,
        fake_node_repo: FakeNodeRepo,
    ) -> None:
        """Test removing node from binder with file deletion."""
        # Arrange: Binder with node, delete_files=True
        node_id = NodeId.generate()

        # Create node in both binder and node repository
        fake_node_repo.create(node_id, 'Test Node', None)

        # Create binder with the node
        binder = Binder(roots=[BinderItem(id_=node_id, display_title='Test Node', children=[])])
        fake_binder_repo.save(binder)

        # Act: Execute RemoveNode with file deletion
        remove_node.execute(node_id, delete_files=True)

        # Assert: Node removed from binder, files deleted from disk
        updated_binder = fake_binder_repo.load()
        assert len(updated_binder.roots) == 0
        assert fake_node_repo.delete_called_with(node_id, delete_files=True)

    def test_remove_node_promotes_children(
        self,
        remove_node: RemoveNode,
        fake_binder_repo: FakeBinderRepo,
    ) -> None:
        """Test removing node promotes children to parent level."""
        # Arrange: Binder with parent node containing children
        parent_id = NodeId.generate()
        child1_id = NodeId.generate()
        child2_id = NodeId.generate()

        child1 = BinderItem(id_=child1_id, display_title='Child 1', children=[])
        child2 = BinderItem(id_=child2_id, display_title='Child 2', children=[])
        parent = BinderItem(id_=parent_id, display_title='Parent', children=[child1, child2])

        binder = Binder(roots=[parent])
        fake_binder_repo.save(binder)

        # Act: Execute RemoveNode on parent
        remove_node.execute(parent_id, delete_files=False)

        # Assert: Children promoted to grandparent level, order preserved
        updated_binder = fake_binder_repo.load()
        assert len(updated_binder.roots) == 2
        assert updated_binder.roots[0].id == child1_id
        assert updated_binder.roots[1].id == child2_id
        assert updated_binder.roots[0].display_title == 'Child 1'
        assert updated_binder.roots[1].display_title == 'Child 2'

    def test_remove_node_promotes_children_nested(
        self,
        remove_node: RemoveNode,
        fake_binder_repo: FakeBinderRepo,
    ) -> None:
        """Test removing nested node promotes children to grandparent level."""
        # Arrange: Binder with grandparent -> parent -> children structure
        grandparent_id = NodeId.generate()
        parent_id = NodeId.generate()
        child1_id = NodeId.generate()
        child2_id = NodeId.generate()

        child1 = BinderItem(id_=child1_id, display_title='Child 1', children=[])
        child2 = BinderItem(id_=child2_id, display_title='Child 2', children=[])
        parent = BinderItem(id_=parent_id, display_title='Parent', children=[child1, child2])
        grandparent = BinderItem(id_=grandparent_id, display_title='Grandparent', children=[parent])

        binder = Binder(roots=[grandparent])
        fake_binder_repo.save(binder)

        # Act: Execute RemoveNode on parent
        remove_node.execute(parent_id, delete_files=False)

        # Assert: Children promoted to grandparent level, order preserved
        updated_binder = fake_binder_repo.load()
        assert len(updated_binder.roots) == 1
        grandparent_item = updated_binder.roots[0]
        assert grandparent_item.id == grandparent_id
        assert len(grandparent_item.children) == 2
        assert grandparent_item.children[0].id == child1_id
        assert grandparent_item.children[1].id == child2_id

    def test_remove_root_level_node(
        self,
        remove_node: RemoveNode,
        fake_binder_repo: FakeBinderRepo,
    ) -> None:
        """Test removing node at root level."""
        # Arrange: Binder with multiple nodes at root level
        node1_id = NodeId.generate()
        node2_id = NodeId.generate()
        node3_id = NodeId.generate()

        node1 = BinderItem(id_=node1_id, display_title='Node 1', children=[])
        node2 = BinderItem(id_=node2_id, display_title='Node 2', children=[])
        node3 = BinderItem(id_=node3_id, display_title='Node 3', children=[])

        binder = Binder(roots=[node1, node2, node3])
        fake_binder_repo.save(binder)

        # Act: Execute RemoveNode on middle root node
        remove_node.execute(node2_id, delete_files=False)

        # Assert: Node removed from binder roots, others remain
        updated_binder = fake_binder_repo.load()
        assert len(updated_binder.roots) == 2
        assert updated_binder.roots[0].id == node1_id
        assert updated_binder.roots[1].id == node3_id

    def test_remove_node_validates_existence(
        self,
        remove_node: RemoveNode,
        fake_binder_repo: FakeBinderRepo,
    ) -> None:
        """Test removing non-existent node raises NodeNotFoundError."""
        # Arrange: Binder without specified NodeId
        binder = Binder(roots=[])
        fake_binder_repo.save(binder)
        non_existent_id = NodeId.generate()

        # Act & Assert: Execute RemoveNode with non-existent node
        with pytest.raises(NodeNotFoundError) as exc_info:
            remove_node.execute(non_existent_id, delete_files=False)

        assert 'Node not found in binder' in str(exc_info.value)
        assert str(non_existent_id) in str(exc_info.value)

    def test_remove_node_deep_nested_recursive_search(
        self,
        remove_node: RemoveNode,
        fake_binder_repo: FakeBinderRepo,
    ) -> None:
        """Test removing deeply nested node to trigger recursive parent search."""
        # Create a complex hierarchy with multiple branches to force recursive search
        root_id = NodeId.generate()
        branch1_id = NodeId.generate()
        branch2_id = NodeId.generate()
        subbranch1_id = NodeId.generate()
        subbranch2_id = NodeId.generate()
        target_id = NodeId.generate()
        child1_id = NodeId.generate()
        child2_id = NodeId.generate()

        # Build complex hierarchy:
        # root
        #   ├── branch1
        #   │   └── subbranch1
        #   └── branch2
        #       └── subbranch2
        #           └── target (with children to promote)
        #               ├── child1
        #               └── child2

        child1 = BinderItem(id_=child1_id, display_title='Child 1', children=[])
        child2 = BinderItem(id_=child2_id, display_title='Child 2', children=[])
        target = BinderItem(id_=target_id, display_title='Target', children=[child1, child2])
        subbranch2 = BinderItem(id_=subbranch2_id, display_title='SubBranch 2', children=[target])
        subbranch1 = BinderItem(id_=subbranch1_id, display_title='SubBranch 1', children=[])
        branch1 = BinderItem(id_=branch1_id, display_title='Branch 1', children=[subbranch1])
        branch2 = BinderItem(id_=branch2_id, display_title='Branch 2', children=[subbranch2])
        root = BinderItem(id_=root_id, display_title='Root', children=[branch1, branch2])

        binder = Binder(roots=[root])
        fake_binder_repo.save(binder)

        # Remove the deeply nested target node - this will trigger recursive search
        # as it needs to search through branch1 first (won't find it), then branch2
        remove_node.execute(target_id, delete_files=False)

        # Verify node was removed and children promoted
        updated_binder = fake_binder_repo.load()
        assert len(updated_binder.roots) == 1

        # Navigate to where target was and verify children were promoted
        root_item = updated_binder.roots[0]
        branch2_item = root_item.children[1]  # branch2
        subbranch2_item = branch2_item.children[0]  # subbranch2

        # Target's children should now be directly under subbranch2
        assert len(subbranch2_item.children) == 2
        assert subbranch2_item.children[0].id == child1_id
        assert subbranch2_item.children[1].id == child2_id

    def test_remove_node_logs_operations(
        self,
        remove_node: RemoveNode,
        fake_binder_repo: FakeBinderRepo,
        fake_node_repo: FakeNodeRepo,
        fake_logger: FakeLogger,
    ) -> None:
        """Test that removal operations are properly logged."""
        # Arrange: Binder with node
        node_id = NodeId.generate()

        # Create node in both binder and node repository
        fake_node_repo.create(node_id, 'Test Node', None)

        binder = Binder(roots=[BinderItem(id_=node_id, display_title='Test Node', children=[])])
        fake_binder_repo.save(binder)

        # Act: Execute RemoveNode
        remove_node.execute(node_id, delete_files=True)

        # Assert: Check that operations were logged
        logged_messages = fake_logger.get_logged_messages()
        assert any('Starting node removal' in msg for msg in logged_messages)
        assert any(str(node_id) in msg for msg in logged_messages)
        assert any('delete_files=True' in msg for msg in logged_messages)

    def test_remove_node_debug_logging(
        self,
        remove_node: RemoveNode,
        fake_binder_repo: FakeBinderRepo,
        fake_logger: FakeLogger,
    ) -> None:
        """Test that detailed debug logs are generated during node removal."""
        # Arrange: Binder with nested node structure
        parent_id = NodeId.generate()
        child1_id = NodeId.generate()
        child2_id = NodeId.generate()

        child1 = BinderItem(id_=child1_id, display_title='Child 1', children=[])
        child2 = BinderItem(id_=child2_id, display_title='Child 2', children=[])
        parent = BinderItem(id_=parent_id, display_title='Parent', children=[child1, child2])

        binder = Binder(roots=[parent])
        fake_binder_repo.save(binder)

        # Act: Execute RemoveNode
        remove_node.execute(parent_id, delete_files=False)

        # Assert: Check debug logs
        logged_messages = fake_logger.get_logged_messages()
        assert any('Preparing to promote children' in msg for msg in logged_messages)
        assert any('Promoting 2 children of ' + str(parent_id) in msg for msg in logged_messages)

    def test_remove_node_empty_children_no_logging(
        self,
        remove_node: RemoveNode,
        fake_binder_repo: FakeBinderRepo,
        fake_logger: FakeLogger,
    ) -> None:
        """Test logging behavior when removing node with no children."""
        # Arrange: Binder with node that has no children
        node_id = NodeId.generate()
        node = BinderItem(id_=node_id, display_title='Leaf Node', children=[])

        binder = Binder(roots=[node])
        fake_binder_repo.save(binder)

        # Act: Execute RemoveNode
        remove_node.execute(node_id, delete_files=False)

        # Assert: No debug log messages about promoting children
        logged_messages = fake_logger.get_logged_messages()
        assert not any('Promoting children' in msg for msg in logged_messages)
