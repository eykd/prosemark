"""Tests for AddNode use case interactor."""

import pytest

from prosemark.adapters.fake_clock import FakeClock
from prosemark.adapters.fake_id_generator import FakeIdGenerator
from prosemark.adapters.fake_logger import FakeLogger
from prosemark.adapters.fake_node_repo import FakeNodeRepo
from prosemark.adapters.fake_storage import FakeBinderRepo
from prosemark.app.use_cases import AddNode
from prosemark.domain.models import Binder, BinderItem, NodeId
from prosemark.exceptions import NodeNotFoundError


class TestAddNode:
    """Test AddNode use case interactor."""

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
        fake_logger: FakeLogger,
        fake_clock: FakeClock,
    ) -> AddNode:
        """AddNode instance with fake dependencies."""
        return AddNode(
            binder_repo=fake_binder_repo,
            node_repo=fake_node_repo,
            id_generator=fake_id_generator,
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
        parent_item = BinderItem(id_=parent_id, display_title='Parent Chapter', children=[])
        binder = Binder(roots=[parent_item])
        fake_binder_repo.save(binder)
        return binder

    def test_add_node_creates_root_level_node(
        self,
        add_node: AddNode,
        fake_binder_repo: FakeBinderRepo,
        fake_node_repo: FakeNodeRepo,
        fake_id_generator: FakeIdGenerator,
        fake_logger: FakeLogger,
        empty_binder: Binder,
    ) -> None:
        """Test AddNode creates root-level node without parent specification."""
        # Arrange
        title = 'Chapter One'
        synopsis = 'The beginning of the story'

        # Act
        result_id = add_node.execute(title=title, synopsis=synopsis, parent_id=None, position=None)

        # Assert - Node ID was generated and returned
        expected_id = NodeId('0192f0c1-0000-7000-8000-000000000001')
        assert result_id == expected_id

        # Assert - Node files were created with proper content
        assert fake_node_repo.node_exists(expected_id)
        frontmatter = fake_node_repo.read_frontmatter(expected_id)
        assert frontmatter['id'] == str(expected_id)
        assert frontmatter['title'] == title
        assert frontmatter['synopsis'] == synopsis
        assert frontmatter['created'] == '2025-09-14T12:00:00Z'
        assert frontmatter['updated'] == '2025-09-14T12:00:00Z'

        # Assert - Node added to binder roots
        updated_binder = fake_binder_repo.load()
        assert len(updated_binder.roots) == 1
        root_item = updated_binder.roots[0]
        assert root_item.id == expected_id
        assert root_item.display_title == title
        assert root_item.children == []

        # Assert - Operations were logged
        assert fake_logger.has_logged('info', 'Starting node creation')
        assert fake_logger.has_logged('info', 'Node creation completed successfully')
        assert fake_logger.has_logged('debug', 'Generated new NodeId')
        assert fake_logger.has_logged('debug', 'Created node files')
        assert fake_logger.has_logged('debug', 'Added node to binder')

    def test_add_node_creates_nested_node(
        self,
        add_node: AddNode,
        fake_binder_repo: FakeBinderRepo,
        fake_node_repo: FakeNodeRepo,
        fake_id_generator: FakeIdGenerator,
        fake_logger: FakeLogger,
        binder_with_nodes: Binder,
    ) -> None:
        """Test AddNode creates nested node under specified parent."""
        # Arrange
        parent_id = NodeId('0192f0c1-1111-7000-8000-000000000001')
        title = 'Section 1.1'
        synopsis = 'First section of the chapter'

        # Act
        result_id = add_node.execute(title=title, synopsis=synopsis, parent_id=parent_id, position=None)

        # Assert - Node was created
        expected_id = NodeId('0192f0c1-0000-7000-8000-000000000001')
        assert result_id == expected_id

        # Assert - Node files were created
        assert fake_node_repo.node_exists(expected_id)
        frontmatter = fake_node_repo.read_frontmatter(expected_id)
        assert frontmatter['title'] == title

        # Assert - Node added under parent in binder hierarchy
        updated_binder = fake_binder_repo.load()
        assert len(updated_binder.roots) == 1
        parent_item = updated_binder.roots[0]
        assert parent_item.id == parent_id
        assert len(parent_item.children) == 1

        child_item = parent_item.children[0]
        assert child_item.id == expected_id
        assert child_item.display_title == title
        assert child_item.children == []

        # Assert - Hierarchy maintenance was logged
        assert fake_logger.has_logged('debug', 'Adding node under parent')

    def test_add_node_generates_proper_node_files(
        self,
        add_node: AddNode,
        fake_node_repo: FakeNodeRepo,
        fake_clock: FakeClock,
        empty_binder: Binder,
    ) -> None:
        """Test AddNode generates node files with correct frontmatter."""
        # Arrange
        title = 'Test Node'
        synopsis = 'Test synopsis'

        # Act
        result_id = add_node.execute(title=title, synopsis=synopsis, parent_id=None, position=None)

        # Assert - Node files created with proper frontmatter structure
        frontmatter = fake_node_repo.read_frontmatter(result_id)

        # Assert all required frontmatter fields are present
        assert 'id' in frontmatter
        assert 'title' in frontmatter
        assert 'synopsis' in frontmatter
        assert 'created' in frontmatter
        assert 'updated' in frontmatter

        # Assert frontmatter values are correct
        assert frontmatter['id'] == str(result_id)
        assert frontmatter['title'] == title
        assert frontmatter['synopsis'] == synopsis
        assert frontmatter['created'] == fake_clock.now_iso()
        assert frontmatter['updated'] == fake_clock.now_iso()

    def test_add_node_updates_binder_structure(
        self,
        add_node: AddNode,
        fake_binder_repo: FakeBinderRepo,
        empty_binder: Binder,
    ) -> None:
        """Test AddNode properly loads, updates, and saves binder."""
        # Arrange
        title = 'Test Node'

        # Act
        result_id = add_node.execute(title=title, synopsis=None, parent_id=None, position=None)

        # Assert - Binder was loaded, updated, and saved
        updated_binder = fake_binder_repo.load()
        assert len(updated_binder.roots) == 1

        new_item = updated_binder.roots[0]
        assert new_item.id == result_id
        assert new_item.display_title == title
        assert new_item.children == []

    def test_add_node_validates_parent_exists(
        self,
        add_node: AddNode,
        fake_logger: FakeLogger,
        empty_binder: Binder,
    ) -> None:
        """Test AddNode validates parent node exists when specified."""
        # Arrange
        non_existent_parent = NodeId('0192f0c1-9999-7000-8000-000000000999')
        title = 'Child Node'

        # Act & Assert
        with pytest.raises(NodeNotFoundError) as exc_info:
            add_node.execute(title=title, synopsis=None, parent_id=non_existent_parent, position=None)

        assert 'Parent node not found' in str(exc_info.value)
        assert str(non_existent_parent) in str(exc_info.value)

        # Assert error was logged
        assert fake_logger.has_logged('error', 'Parent node not found in binder')

    def test_add_node_handles_none_synopsis(
        self,
        add_node: AddNode,
        fake_node_repo: FakeNodeRepo,
        empty_binder: Binder,
    ) -> None:
        """Test AddNode handles None synopsis correctly."""
        # Arrange
        title = 'Node Without Synopsis'

        # Act
        result_id = add_node.execute(title=title, synopsis=None, parent_id=None, position=None)

        # Assert - Node created with None synopsis
        frontmatter = fake_node_repo.read_frontmatter(result_id)
        assert frontmatter['synopsis'] is None

    def test_add_node_handles_none_title(
        self,
        add_node: AddNode,
        fake_node_repo: FakeNodeRepo,
        fake_binder_repo: FakeBinderRepo,
        empty_binder: Binder,
    ) -> None:
        """Test AddNode handles None title correctly."""
        # Arrange
        synopsis = 'Synopsis without title'

        # Act
        result_id = add_node.execute(title=None, synopsis=synopsis, parent_id=None, position=None)

        # Assert - Node created with None title
        frontmatter = fake_node_repo.read_frontmatter(result_id)
        assert frontmatter['title'] is None

        # Assert - Display title defaults to (untitled) for None title
        updated_binder = fake_binder_repo.load()
        new_item = updated_binder.roots[0]
        assert new_item.display_title == '(untitled)'

    def test_add_node_uses_title_as_display_title(
        self,
        add_node: AddNode,
        fake_binder_repo: FakeBinderRepo,
        empty_binder: Binder,
    ) -> None:
        """Test AddNode uses title as display_title in BinderItem."""
        # Arrange
        title = 'Display Title Test'

        # Act
        add_node.execute(title=title, synopsis=None, parent_id=None, position=None)

        # Assert - BinderItem uses title as display_title
        updated_binder = fake_binder_repo.load()
        new_item = updated_binder.roots[0]
        assert new_item.display_title == title

    def test_add_node_supports_position_parameter(
        self,
        add_node: AddNode,
        fake_binder_repo: FakeBinderRepo,
        empty_binder: Binder,
    ) -> None:
        """Test AddNode supports position parameter for insertion order."""
        # Arrange - Add first node
        first_title = 'First Node'
        first_id = add_node.execute(title=first_title, synopsis=None, parent_id=None, position=None)

        # Act - Add second node at position 0 (beginning)
        second_title = 'Second Node (at beginning)'
        second_id = add_node.execute(title=second_title, synopsis=None, parent_id=None, position=0)

        # Assert - Second node was inserted at the beginning
        updated_binder = fake_binder_repo.load()
        assert len(updated_binder.roots) == 2
        assert updated_binder.roots[0].id == second_id
        assert updated_binder.roots[0].display_title == second_title
        assert updated_binder.roots[1].id == first_id
        assert updated_binder.roots[1].display_title == first_title

    def test_add_node_supports_position_parameter_with_parent(
        self,
        add_node: AddNode,
        fake_binder_repo: FakeBinderRepo,
        binder_with_nodes: Binder,
    ) -> None:
        """Test AddNode supports position parameter when adding under a parent."""
        # Arrange - Add first child to parent
        parent_id = NodeId('0192f0c1-1111-7000-8000-000000000001')
        first_child_title = 'First Child'
        first_child_id = add_node.execute(title=first_child_title, synopsis=None, parent_id=parent_id, position=None)

        # Act - Add second child at position 0 (beginning of parent's children)
        second_child_title = 'Second Child (at beginning)'
        second_child_id = add_node.execute(title=second_child_title, synopsis=None, parent_id=parent_id, position=0)

        # Assert - Second child was inserted at the beginning of parent's children
        updated_binder = fake_binder_repo.load()
        parent_item = updated_binder.roots[0]
        assert len(parent_item.children) == 2
        assert parent_item.children[0].id == second_child_id
        assert parent_item.children[0].display_title == second_child_title
        assert parent_item.children[1].id == first_child_id
        assert parent_item.children[1].display_title == first_child_title

    def test_add_node_logs_node_creation_actions(
        self,
        add_node: AddNode,
        fake_logger: FakeLogger,
        empty_binder: Binder,
    ) -> None:
        """Test AddNode logs all node creation actions with NodeId for traceability."""
        # Arrange
        title = 'Logged Node'
        expected_id = NodeId('0192f0c1-0000-7000-8000-000000000001')

        # Act
        result_id = add_node.execute(title=title, synopsis=None, parent_id=None, position=None)

        # Assert - All major operations were logged with NodeId
        assert result_id == expected_id

        # Check for specific log messages with NodeId traceability
        assert fake_logger.has_logged('info', 'Starting node creation')
        assert fake_logger.has_logged('debug', 'Generated new NodeId')
        assert fake_logger.has_logged('debug', 'Created node files')
        assert fake_logger.has_logged('debug', 'Added node to binder')
        assert fake_logger.has_logged('info', 'Node creation completed successfully')

        # Verify NodeId appears in log context (implementation detail)
        logs = fake_logger.get_logs()
        assert any(str(expected_id) in str(log) for log in logs if 'NodeId' in str(log[1]))

    def test_add_node_maintains_binder_integrity(
        self,
        add_node: AddNode,
        fake_binder_repo: FakeBinderRepo,
        binder_with_nodes: Binder,
    ) -> None:
        """Test AddNode maintains binder integrity after node addition."""
        # Arrange
        parent_id = NodeId('0192f0c1-1111-7000-8000-000000000001')
        title = 'Integrity Test Node'

        # Act
        result_id = add_node.execute(title=title, synopsis=None, parent_id=parent_id, position=None)

        # Assert - Binder integrity is maintained
        updated_binder = fake_binder_repo.load()

        # Validate no duplicate IDs
        all_ids = updated_binder.get_all_node_ids()
        assert len(all_ids) == 2  # Parent + new child
        assert parent_id in all_ids
        assert result_id in all_ids

        # Validate tree structure
        assert len(updated_binder.roots) == 1
        parent_item = updated_binder.roots[0]
        assert len(parent_item.children) == 1
        child_item = parent_item.children[0]
        assert child_item.id == result_id

    def test_add_node_uses_injected_dependencies(
        self,
        fake_binder_repo: FakeBinderRepo,
        fake_node_repo: FakeNodeRepo,
        fake_id_generator: FakeIdGenerator,
        fake_logger: FakeLogger,
        fake_clock: FakeClock,
    ) -> None:
        """Test AddNode uses all injected dependencies correctly."""
        # Arrange
        add_node = AddNode(
            binder_repo=fake_binder_repo,
            node_repo=fake_node_repo,
            id_generator=fake_id_generator,
            logger=fake_logger,
            clock=fake_clock,
        )
        empty_binder = Binder(roots=[])
        fake_binder_repo.save(empty_binder)

        title = 'Dependency Test'

        # Act
        result_id = add_node.execute(title=title, synopsis=None, parent_id=None, position=None)

        # Assert all dependencies were used
        # IdGenerator generated expected ID
        expected_id = NodeId('0192f0c1-0000-7000-8000-000000000001')
        assert result_id == expected_id

        # NodeRepo created the node
        assert fake_node_repo.node_exists(result_id)

        # BinderRepo was updated
        updated_binder = fake_binder_repo.load()
        assert len(updated_binder.roots) == 1

        # Logger recorded operations
        assert fake_logger.log_count() > 0

        # Clock timestamp was used (indirectly through NodeRepo)
        frontmatter = fake_node_repo.read_frontmatter(result_id)
        assert frontmatter['created'] == fake_clock.now_iso()
        assert frontmatter['updated'] == fake_clock.now_iso()
