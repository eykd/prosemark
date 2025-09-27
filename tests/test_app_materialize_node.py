"""Tests for MaterializeNode use case interactor."""

import pytest

from prosemark.adapters.fake_clock import FakeClock
from prosemark.adapters.fake_console import FakeConsolePort
from prosemark.adapters.fake_id_generator import FakeIdGenerator
from prosemark.adapters.fake_logger import FakeLogger
from prosemark.adapters.fake_node_repo import FakeNodeRepo
from prosemark.adapters.fake_storage import FakeBinderRepo
from prosemark.app.materialize_node import MaterializeNode
from prosemark.domain.models import Binder, BinderItem, NodeId
from prosemark.exceptions import PlaceholderNotFoundError


class TestMaterializeNode:
    """Test MaterializeNode use case interactor."""

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
    def fake_console(self) -> FakeConsolePort:
        """Fake Console for testing."""
        return FakeConsolePort()

    @pytest.fixture
    def fake_clock(self) -> FakeClock:
        """Fake Clock for testing."""
        return FakeClock()

    @pytest.fixture
    def materialize_node(
        self,
        fake_binder_repo: FakeBinderRepo,
        fake_node_repo: FakeNodeRepo,
        fake_id_generator: FakeIdGenerator,
        fake_clock: FakeClock,
        fake_console: FakeConsolePort,
        fake_logger: FakeLogger,
    ) -> MaterializeNode:
        """MaterializeNode instance with fake dependencies."""
        return MaterializeNode(
            binder_repo=fake_binder_repo,
            node_repo=fake_node_repo,
            id_generator=fake_id_generator,
            clock=fake_clock,
            console=fake_console,
            logger=fake_logger,
        )

    @pytest.fixture
    def binder_with_placeholder(self, fake_binder_repo: FakeBinderRepo) -> Binder:
        """Binder with a placeholder item."""
        placeholder = BinderItem(id_=None, display_title='New Chapter', children=[])
        binder = Binder(roots=[placeholder])
        fake_binder_repo.save(binder)
        return binder

    @pytest.fixture
    def binder_with_mixed_items(self, fake_binder_repo: FakeBinderRepo) -> Binder:
        """Binder with both placeholders and materialized items."""
        existing_id = NodeId('0192f0c1-1111-7000-8000-000000000001')
        existing_item = BinderItem(id_=existing_id, display_title='Existing Chapter', children=[])
        placeholder = BinderItem(id_=None, display_title='Placeholder Chapter', children=[])
        binder = Binder(roots=[existing_item, placeholder])
        fake_binder_repo.save(binder)
        return binder

    @pytest.fixture
    def binder_with_nested_placeholder(self, fake_binder_repo: FakeBinderRepo) -> Binder:
        """Binder with placeholder nested under an existing node."""
        parent_id = NodeId('0192f0c1-1111-7000-8000-000000000001')
        nested_placeholder = BinderItem(id_=None, display_title='Nested Section', children=[])
        parent_item = BinderItem(id_=parent_id, display_title='Parent Chapter', children=[nested_placeholder])
        binder = Binder(roots=[parent_item])
        fake_binder_repo.save(binder)
        return binder

    def test_successful_placeholder_materialization(
        self,
        materialize_node: MaterializeNode,
        fake_binder_repo: FakeBinderRepo,
        fake_node_repo: FakeNodeRepo,
        fake_id_generator: FakeIdGenerator,
        binder_with_placeholder: Binder,
    ) -> None:
        """Test successful placeholder materialization."""
        # Arrange
        display_title = 'New Chapter'

        # Act
        result = materialize_node.execute(title=display_title)

        # Assert - Node ID was generated and returned
        expected_id = NodeId('0192f0c1-0000-7000-8000-000000000001')
        assert result.node_id == expected_id
        assert not result.was_already_materialized

        # Assert - Node files were created
        assert fake_node_repo.node_exists(expected_id)

        # Assert - Binder was updated with new node ID
        updated_binder = fake_binder_repo.load()
        materialized_item = updated_binder.find_by_id(expected_id)
        assert materialized_item is not None
        assert materialized_item.display_title == display_title
        assert materialized_item.id == expected_id

        # Assert - No placeholders remain with that title
        placeholder = updated_binder.find_placeholder_by_display_title(display_title)
        assert placeholder is None

    def test_materialization_with_custom_synopsis(
        self,
        materialize_node: MaterializeNode,
        fake_node_repo: FakeNodeRepo,
        binder_with_placeholder: Binder,
    ) -> None:
        """Test materialization creates node with None synopsis."""
        # Arrange
        display_title = 'New Chapter'

        # Act
        materialize_node.execute(title=display_title)

        # Assert - Node was created with None synopsis (current behavior)
        expected_id = NodeId('0192f0c1-0000-7000-8000-000000000001')
        frontmatter = fake_node_repo.read_frontmatter(expected_id)
        assert frontmatter['synopsis'] is None

    def test_placeholder_not_found_error(
        self,
        materialize_node: MaterializeNode,
        binder_with_placeholder: Binder,
    ) -> None:
        """Test placeholder not found error."""
        # Arrange
        nonexistent_title = 'Nonexistent Chapter'

        # Act & Assert
        with pytest.raises(PlaceholderNotFoundError, match=r'Item.*not found'):
            materialize_node.execute(title=nonexistent_title)

    def test_materialization_of_already_materialized_item(
        self,
        materialize_node: MaterializeNode,
        binder_with_mixed_items: Binder,
        fake_node_repo: FakeNodeRepo,
        fake_logger: FakeLogger,
    ) -> None:
        """Test materialization of already materialized item."""
        # Arrange
        existing_title = 'Existing Chapter'

        # Simulate that the notes file is missing (don't include it in existing notes files)
        existing_node_id = NodeId('0192f0c1-1111-7000-8000-000000000001')
        fake_node_repo.set_existing_notes_files([])  # No notes files exist

        # Act - Should handle already materialized item and create missing notes file
        result = materialize_node.execute(title=existing_title)

        # Assert - Should return existing node ID
        assert result.node_id == existing_node_id

        # Assert - Notes file should have been created in the fake repo
        assert fake_node_repo.file_exists(existing_node_id, 'notes')

    def test_binder_update_after_materialization(
        self,
        materialize_node: MaterializeNode,
        fake_binder_repo: FakeBinderRepo,
        binder_with_placeholder: Binder,
    ) -> None:
        """Test binder update after materialization."""
        # Arrange
        display_title = 'New Chapter'

        # Act
        result = materialize_node.execute(title=display_title)

        # Assert - Binder was reloaded and placeholder is replaced
        reloaded_binder = fake_binder_repo.load()
        materialized_item = reloaded_binder.find_by_id(result.node_id)
        assert materialized_item is not None
        assert materialized_item.display_title == display_title

        # Assert - No placeholder with that title exists
        placeholder = reloaded_binder.find_placeholder_by_display_title(display_title)
        assert placeholder is None

    def test_file_system_integration(
        self,
        materialize_node: MaterializeNode,
        fake_node_repo: FakeNodeRepo,
        binder_with_placeholder: Binder,
    ) -> None:
        """Test file system integration."""
        # Arrange
        display_title = 'New Chapter'

        # Act
        materialize_node.execute(title=display_title)

        # Assert - Both draft and notes files exist
        expected_id = NodeId('0192f0c1-0000-7000-8000-000000000001')
        assert fake_node_repo.node_exists(expected_id)

        # Check that create was called with proper parameters
        frontmatter = fake_node_repo.read_frontmatter(expected_id)
        assert frontmatter['title'] == display_title
        assert frontmatter['synopsis'] is None

    def test_nested_placeholder_materialization(
        self,
        materialize_node: MaterializeNode,
        fake_binder_repo: FakeBinderRepo,
        binder_with_nested_placeholder: Binder,
    ) -> None:
        """Test materialization preserves hierarchical position."""
        # Arrange
        display_title = 'Nested Section'

        # Act
        result = materialize_node.execute(title=display_title)

        # Assert - Hierarchy is preserved
        updated_binder = fake_binder_repo.load()
        parent_id = NodeId('0192f0c1-1111-7000-8000-000000000001')
        parent_item = updated_binder.find_by_id(parent_id)
        assert parent_item is not None

        # Assert - Materialized item is now a child of the parent
        assert len(parent_item.children) == 1
        materialized_child = parent_item.children[0]
        assert materialized_child.id == result.node_id
        assert materialized_child.display_title == display_title

    def test_materialization_preserves_title_as_display_title(
        self,
        materialize_node: MaterializeNode,
        fake_binder_repo: FakeBinderRepo,
        binder_with_placeholder: Binder,
    ) -> None:
        """Test that materialization preserves display title."""
        # Arrange
        display_title = 'New Chapter'

        # Act
        result = materialize_node.execute(title=display_title)

        # Assert - Display title is preserved in binder
        updated_binder = fake_binder_repo.load()
        materialized_item = updated_binder.find_by_id(result.node_id)
        assert materialized_item is not None
        assert materialized_item.display_title == display_title

    def test_multiple_placeholders_with_same_title(
        self,
        materialize_node: MaterializeNode,
        fake_binder_repo: FakeBinderRepo,
    ) -> None:
        """Test behavior when multiple placeholders have the same title."""
        # Arrange - Create binder with two placeholders with same title
        placeholder1 = BinderItem(id_=None, display_title='Same Title', children=[])
        placeholder2 = BinderItem(id_=None, display_title='Same Title', children=[])
        binder = Binder(roots=[placeholder1, placeholder2])
        fake_binder_repo.save(binder)

        # Act - Materialize one of them
        result = materialize_node.execute(title='Same Title')

        # Assert - Only one was materialized (first found)
        updated_binder = fake_binder_repo.load()
        materialized_item = updated_binder.find_by_id(result.node_id)
        assert materialized_item is not None

        # Assert - One placeholder still remains
        remaining_placeholder = updated_binder.find_placeholder_by_display_title('Same Title')
        assert remaining_placeholder is not None

    def test_deeply_nested_placeholder_materialization(
        self,
        materialize_node: MaterializeNode,
        fake_binder_repo: FakeBinderRepo,
    ) -> None:
        """Test materialization of deeply nested placeholder through recursive search."""
        # Arrange - Create a deeply nested structure with placeholder at the bottom
        deep_placeholder = BinderItem(id_=None, display_title='Deep Placeholder', children=[])
        level3 = BinderItem(
            id_=NodeId('0192f0c1-3333-7000-8000-000000000003'),
            display_title='Level 3',
            children=[deep_placeholder],
        )
        level2 = BinderItem(
            id_=NodeId('0192f0c1-2222-7000-8000-000000000002'),
            display_title='Level 2',
            children=[level3],
        )
        level1 = BinderItem(
            id_=NodeId('0192f0c1-1111-7000-8000-000000000001'),
            display_title='Level 1',
            children=[level2],
        )
        binder = Binder(roots=[level1])
        fake_binder_repo.save(binder)

        # Act - Materialize the deeply nested placeholder
        result = materialize_node.execute(title='Deep Placeholder')

        # Assert - Placeholder was found and materialized
        updated_binder = fake_binder_repo.load()
        materialized_item = updated_binder.find_by_id(result.node_id)
        assert materialized_item is not None
        assert materialized_item.display_title == 'Deep Placeholder'

    def test_already_materialized_in_nested_structure(
        self,
        materialize_node: MaterializeNode,
        fake_binder_repo: FakeBinderRepo,
        fake_node_repo: FakeNodeRepo,
        fake_logger: FakeLogger,
    ) -> None:
        """Test error when trying to materialize an already materialized nested item."""
        # Arrange - Create nested structure with materialized item deep in hierarchy
        existing_id = NodeId('0192f0c1-4444-7000-8000-000000000004')
        materialized_item = BinderItem(
            id_=existing_id,
            display_title='Already Materialized',
            children=[],
        )
        parent = BinderItem(
            id_=NodeId('0192f0c1-1111-7000-8000-000000000001'),
            display_title='Parent',
            children=[materialized_item],
        )
        binder = Binder(roots=[parent])
        fake_binder_repo.save(binder)

        # Simulate that the notes file exists (no missing notes file to create)
        fake_node_repo.set_existing_notes_files([str(existing_id)])

        # Act - Should handle already materialized item that has notes file
        result = materialize_node.execute(title='Already Materialized')

        # Assert - Should return existing node ID
        assert result.node_id == existing_id

    def test_recursive_search_through_multiple_branches(
        self,
        materialize_node: MaterializeNode,
        fake_binder_repo: FakeBinderRepo,
    ) -> None:
        """Test recursive search continues through multiple children branches."""
        # Arrange - Create structure where target is in second branch
        # This tests the loop continuation in _find_item_by_title_recursive
        target_placeholder = BinderItem(id_=None, display_title='Target Placeholder', children=[])

        # First branch with no match
        branch1_child = BinderItem(
            id_=NodeId('0192f0c1-1111-7000-8000-000000000001'),
            display_title='Branch 1 Child',
            children=[],
        )
        branch1 = BinderItem(
            id_=NodeId('0192f0c1-2222-7000-8000-000000000002'),
            display_title='Branch 1',
            children=[branch1_child],
        )

        # Second branch with the target
        branch2 = BinderItem(
            id_=NodeId('0192f0c1-3333-7000-8000-000000000003'),
            display_title='Branch 2',
            children=[target_placeholder],
        )

        # Parent with multiple children branches
        parent = BinderItem(
            id_=NodeId('0192f0c1-4444-7000-8000-000000000004'),
            display_title='Parent',
            children=[branch1, branch2],  # Target is in second branch
        )

        binder = Binder(roots=[parent])
        fake_binder_repo.save(binder)

        # Act - Should find the target in the second branch
        result = materialize_node.execute(title='Target Placeholder')

        # Assert - Target was found and materialized
        updated_binder = fake_binder_repo.load()
        materialized_item = updated_binder.find_by_id(result.node_id)
        assert materialized_item is not None
        assert materialized_item.display_title == 'Target Placeholder'

    def test_recursive_search_with_early_return_from_child(
        self,
        materialize_node: MaterializeNode,
        fake_binder_repo: FakeBinderRepo,
        fake_node_repo: FakeNodeRepo,
    ) -> None:
        """Test recursive search returns early when found in first child's subtree."""
        # This specifically tests the branch at line 1408->1409 where result is not None
        # Create a structure where:
        # - Root has multiple children
        # - Target is deep in the first child's subtree
        # - This ensures the recursive call returns a non-None result that needs to be propagated

        target_item = BinderItem(
            id_=NodeId('0192f0c1-5555-7000-8000-000000000005'),
            display_title='Deep Target',
            children=[],
        )

        # First child has target deep in its subtree
        deep_child = BinderItem(
            id_=NodeId('0192f0c1-6666-7000-8000-000000000006'),
            display_title='Deep Child',
            children=[target_item],
        )
        first_child = BinderItem(
            id_=NodeId('0192f0c1-7777-7000-8000-000000000007'),
            display_title='First Child',
            children=[deep_child],
        )

        # Second child (should not be searched if early return works)
        second_child = BinderItem(
            id_=NodeId('0192f0c1-8888-7000-8000-000000000008'),
            display_title='Second Child',
            children=[],
        )

        # Root with multiple children
        root = BinderItem(
            id_=None,
            display_title='Root',
            children=[first_child, second_child],
        )

        binder = Binder(roots=[root])
        fake_binder_repo.save(binder)

        # Simulate that notes file exists for the target item
        target_id = NodeId('0192f0c1-5555-7000-8000-000000000005')
        fake_node_repo.set_existing_notes_files([str(target_id)])

        # Act - Should handle already materialized item with existing notes file
        result = materialize_node.execute(title='Deep Target')

        # Assert - Should return the target node ID
        assert result.node_id == target_id

    def test_materialization_creates_missing_notes_file(
        self,
        materialize_node: MaterializeNode,
        fake_binder_repo: FakeBinderRepo,
        fake_node_repo: FakeNodeRepo,
        fake_console: FakeConsolePort,
    ) -> None:
        """Test that materialization creates missing notes file for already materialized nodes."""
        # Arrange - Binder with already materialized item
        existing_node_id = NodeId('0192f0c1-1111-7000-8000-000000000001')
        materialized_item = BinderItem(
            id_=existing_node_id,
            display_title='Existing Chapter',
            children=[],
        )
        binder = Binder(roots=[materialized_item])
        fake_binder_repo.save(binder)

        # Simulate that the notes file is missing (not in existing notes files list)
        fake_node_repo.set_existing_notes_files([])

        # Act
        result = materialize_node.execute(title='Existing Chapter')

        # Assert - Should return existing node ID
        assert result.node_id == existing_node_id

        # Assert - Notes file should now exist
        assert fake_node_repo.file_exists(existing_node_id, 'notes')

        # Assert - Success message was printed
        output = fake_console.get_output()
        assert any('Created missing notes file' in msg for msg in output)

    def test_materialization_skips_creation_when_notes_file_exists(
        self,
        materialize_node: MaterializeNode,
        fake_binder_repo: FakeBinderRepo,
        fake_node_repo: FakeNodeRepo,
        fake_console: FakeConsolePort,
    ) -> None:
        """Test that materialization skips notes file creation when it already exists."""
        # Arrange - Binder with already materialized item
        existing_node_id = NodeId('0192f0c1-1111-7000-8000-000000000001')
        materialized_item = BinderItem(
            id_=existing_node_id,
            display_title='Existing Chapter',
            children=[],
        )
        binder = Binder(roots=[materialized_item])
        fake_binder_repo.save(binder)

        # Simulate that the notes file already exists
        fake_node_repo.set_existing_notes_files([str(existing_node_id)])

        # Act
        result = materialize_node.execute(title='Existing Chapter')

        # Assert - Should return existing node ID
        assert result.node_id == existing_node_id

        # Assert - Warning message was printed
        output = fake_console.get_output()
        assert any('is already materialized' in msg for msg in output)
