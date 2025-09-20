"""Advanced tests for RemoveNode use case."""

import pytest

from prosemark.adapters.fake_logger import FakeLogger
from prosemark.adapters.fake_node_repo import FakeNodeRepo
from prosemark.adapters.fake_storage import FakeBinderRepo
from prosemark.app.use_cases import RemoveNode
from prosemark.domain.models import Binder, BinderItem, NodeId


class TestRemoveNodeAdvanced:
    """Advanced test cases for RemoveNode interactor."""

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

    def test_remove_node_complex_hierarchy_promotion(
        self,
        remove_node: RemoveNode,
        fake_binder_repo: FakeBinderRepo,
    ) -> None:
        """Test complex multi-level hierarchy promotion when removing parent nodes."""
        # Create a deep hierarchy
        great_grandparent_id = NodeId.generate()
        grandparent_id = NodeId.generate()
        parent_id = NodeId.generate()
        child1_id = NodeId.generate()
        child2_id = NodeId.generate()

        # Create deep hierarchy
        child1 = BinderItem(id_=child1_id, display_title='Child 1', children=[])
        child2 = BinderItem(id_=child2_id, display_title='Child 2', children=[])
        parent = BinderItem(id_=parent_id, display_title='Parent', children=[child1, child2])
        grandparent = BinderItem(id_=grandparent_id, display_title='Grandparent', children=[parent])
        great_grandparent = BinderItem(
            id_=great_grandparent_id, display_title='Great Grandparent', children=[grandparent]
        )

        binder = Binder(roots=[great_grandparent])
        fake_binder_repo.save(binder)

        # Remove the grandparent
        remove_node.execute(grandparent_id, delete_files=False)

        # Verify hierarchy after removal
        updated_binder = fake_binder_repo.load()
        assert len(updated_binder.roots) == 1

        great_grandparent_item = updated_binder.roots[0]
        assert great_grandparent_item.id == great_grandparent_id

        # Children are nested under the parent
        assert len(great_grandparent_item.children) == 1
        assert great_grandparent_item.children[0].id == parent_id
        assert len(great_grandparent_item.children[0].children) == 2
        assert great_grandparent_item.children[0].children[0].id == child1_id
        assert great_grandparent_item.children[0].children[1].id == child2_id

    def test_remove_node_no_children_root_level(
        self,
        remove_node: RemoveNode,
        fake_binder_repo: FakeBinderRepo,
    ) -> None:
        """Test removing a node with no children at root level."""
        # Create multiple root-level nodes
        node1_id = NodeId.generate()
        node2_id = NodeId.generate()
        node3_id = NodeId.generate()

        node1 = BinderItem(id_=node1_id, display_title='Node 1', children=[])
        node2 = BinderItem(id_=node2_id, display_title='Node 2', children=[])
        node3 = BinderItem(id_=node3_id, display_title='Node 3', children=[])

        binder = Binder(roots=[node1, node2, node3])
        fake_binder_repo.save(binder)

        # Remove middle node
        remove_node.execute(node2_id, delete_files=False)

        # Verify remaining hierarchy
        updated_binder = fake_binder_repo.load()
        assert len(updated_binder.roots) == 2
        assert updated_binder.roots[0].id == node1_id
        assert updated_binder.roots[1].id == node3_id
