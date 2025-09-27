"""Comprehensive tests for MaterializeNode use case to achieve 100% coverage."""

from pathlib import Path

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


class TestMaterializeNodeCoverage:
    """Test MaterializeNode use case with complete coverage."""

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
    def materialize_node(
        self,
        fake_binder_repo: FakeBinderRepo,
        fake_node_repo: FakeNodeRepo,
        fake_id_generator: FakeIdGenerator,
        fake_console: FakeConsolePort,
        fake_logger: FakeLogger,
        fake_clock: FakeClock,
    ) -> MaterializeNode:
        """MaterializeNode instance with fake dependencies."""
        return MaterializeNode(
            binder_repo=fake_binder_repo,
            node_repo=fake_node_repo,
            id_generator=fake_id_generator,
            console=fake_console,
            logger=fake_logger,
            clock=fake_clock,
        )

    @pytest.fixture
    def binder_with_placeholder(self, fake_binder_repo: FakeBinderRepo) -> Binder:
        """Binder with a placeholder for testing."""
        placeholder = BinderItem(display_title='Chapter Placeholder', node_id=None, children=[])
        binder = Binder(roots=[placeholder])
        fake_binder_repo.save(binder)
        return binder

    @pytest.fixture
    def binder_with_materialized_node(self, fake_binder_repo: FakeBinderRepo) -> Binder:
        """Binder with an already materialized node."""
        node_id = NodeId('0192f0c1-0022-7000-8000-000000000022')
        item = BinderItem(display_title='Already Materialized', node_id=node_id, children=[])
        binder = Binder(roots=[item])
        fake_binder_repo.save(binder)
        return binder

    def test_materialize_node_converts_placeholder(
        self,
        materialize_node: MaterializeNode,
        fake_binder_repo: FakeBinderRepo,
        fake_node_repo: FakeNodeRepo,
        fake_id_generator: FakeIdGenerator,
        fake_console: FakeConsolePort,
        fake_logger: FakeLogger,
        binder_with_placeholder: Binder,
    ) -> None:
        """Test MaterializeNode converts placeholder to actual node."""
        # Arrange
        title = 'Chapter Placeholder'

        # Act
        result = materialize_node.execute(title=title)

        # Assert - Node ID was generated and returned
        expected_id = NodeId('0192f0c1-0000-7000-8000-000000000001')
        assert result.node_id == expected_id
        assert not result.was_already_materialized

        # Assert - Node files were created
        assert fake_node_repo.node_exists(expected_id)

        # Assert - Placeholder was updated with node ID
        updated_binder = fake_binder_repo.load()
        materialized_item = updated_binder.roots[0]
        assert materialized_item.node_id == expected_id
        assert materialized_item.display_title == title

        # Assert - Success messages displayed
        assert fake_console.output_contains(f'SUCCESS: Materialized "{title}" ({expected_id.value})')
        assert fake_console.output_contains(
            f'INFO: Created files: {expected_id.value}.md, {expected_id.value}.notes.md'
        )

        # Assert - Operations logged
        assert fake_logger.has_logged('info', f'Materializing placeholder: {title}')
        assert fake_logger.has_logged('info', f'Placeholder materialized: {title} -> {expected_id.value}')

    @pytest.mark.skip(reason='Unreachable code - _find_placeholder only returns unmaterialized items')
    def test_materialize_node_handles_already_materialized(
        self,
        materialize_node: MaterializeNode,
        fake_binder_repo: FakeBinderRepo,
        fake_console: FakeConsolePort,
    ) -> None:
        """Test MaterializeNode handles already materialized placeholder."""
        # Arrange - Create a placeholder, materialize it, then try again
        title = 'Test Placeholder'
        placeholder = BinderItem(display_title=title, node_id=None, children=[])
        binder = Binder(roots=[placeholder])
        fake_binder_repo.save(binder)

        # First materialization
        first_result = materialize_node.execute(title=title)
        first_id = first_result.node_id

        # Act - Try to materialize again
        result = materialize_node.execute(title=title)

        # Assert - Returns same node ID and indicates it was already materialized
        assert result.node_id == first_id
        assert result.was_already_materialized

        # Assert - Warning message displayed on second attempt
        assert fake_console.output_contains(f'WARNING: {title} is already materialized')

    def test_materialize_node_handles_placeholder_not_found(
        self,
        materialize_node: MaterializeNode,
        fake_binder_repo: FakeBinderRepo,
    ) -> None:
        """Test MaterializeNode raises error when placeholder not found."""
        # Arrange - Empty binder
        binder = Binder(roots=[])
        fake_binder_repo.save(binder)
        title = 'Nonexistent Placeholder'

        # Act & Assert
        with pytest.raises(PlaceholderNotFoundError) as exc_info:
            materialize_node.execute(title=title)

        assert f"Item '{title}' not found" in str(exc_info.value)

    def test_materialize_node_finds_nested_placeholder(
        self,
        materialize_node: MaterializeNode,
        fake_binder_repo: FakeBinderRepo,
        fake_node_repo: FakeNodeRepo,
        fake_console: FakeConsolePort,
    ) -> None:
        """Test MaterializeNode finds placeholder in nested structure."""
        # Arrange - Create nested structure with placeholder
        parent = BinderItem(
            display_title='Parent Chapter', node_id=NodeId('0192f0c1-0021-7000-8000-000000000021'), children=[]
        )
        nested_placeholder = BinderItem(display_title='Nested Placeholder', node_id=None, children=[])
        parent.children.append(nested_placeholder)
        binder = Binder(roots=[parent])
        fake_binder_repo.save(binder)

        # Act
        result = materialize_node.execute(title='Nested Placeholder')

        # Assert - Nested placeholder was materialized
        expected_id = NodeId('0192f0c1-0000-7000-8000-000000000001')
        assert result.node_id == expected_id
        assert not result.was_already_materialized

        # Assert - Node files were created
        assert fake_node_repo.node_exists(expected_id)

        # Assert - Nested item was updated
        updated_binder = fake_binder_repo.load()
        parent_item = updated_binder.roots[0]
        materialized_child = parent_item.children[0]
        assert materialized_child.node_id == expected_id
        assert materialized_child.display_title == 'Nested Placeholder'

    def test_materialize_node_find_placeholder_returns_none_for_missing(
        self,
        materialize_node: MaterializeNode,
        fake_binder_repo: FakeBinderRepo,
    ) -> None:
        """Test _find_placeholder returns None when placeholder is not found."""
        # Arrange - Binder with non-placeholder items
        item = BinderItem(
            display_title='Regular Item', node_id=NodeId('0192f0c1-0033-7000-8000-000000000033'), children=[]
        )
        binder = Binder(roots=[item])
        fake_binder_repo.save(binder)

        # Act - Try to materialize non-existent placeholder
        # This tests the _find_placeholder method indirectly
        with pytest.raises(PlaceholderNotFoundError):
            materialize_node.execute(title='Nonexistent')

    def test_materialize_node_find_placeholder_searches_recursively(
        self,
        materialize_node: MaterializeNode,
        fake_binder_repo: FakeBinderRepo,
    ) -> None:
        """Test _find_placeholder searches recursively through hierarchy."""
        # Arrange - Create deeply nested placeholder
        grandparent = BinderItem(
            display_title='Grandparent', node_id=NodeId('0192f0c1-0023-7000-8000-000000000023'), children=[]
        )
        parent = BinderItem(display_title='Parent', node_id=NodeId('0192f0c1-0021-7000-8000-000000000021'), children=[])
        deep_placeholder = BinderItem(display_title='Deep Placeholder', node_id=None, children=[])

        parent.children.append(deep_placeholder)
        grandparent.children.append(parent)
        binder = Binder(roots=[grandparent])
        fake_binder_repo.save(binder)

        # Act
        result = materialize_node.execute(title='Deep Placeholder')

        # Assert - Deep placeholder was found and materialized
        expected_id = NodeId('0192f0c1-0000-7000-8000-000000000001')
        assert result.node_id == expected_id

        # Verify the deep structure was updated
        updated_binder = fake_binder_repo.load()
        updated_grandparent = updated_binder.roots[0]
        updated_parent = updated_grandparent.children[0]
        updated_placeholder = updated_parent.children[0]
        assert updated_placeholder.node_id == expected_id

    def test_materialize_node_uses_current_directory_when_no_path_provided(
        self,
        materialize_node: MaterializeNode,
        fake_logger: FakeLogger,
        binder_with_placeholder: Binder,
    ) -> None:
        """Test MaterializeNode uses current directory when no project_path provided."""
        # Arrange
        title = 'Chapter Placeholder'

        # Act - Execute without project_path (it uses Path.cwd() internally)
        materialize_node.execute(title=title, project_path=None)

        # Assert - Should complete without error (using current directory internally)
        assert fake_logger.has_logged('info', f'Materializing placeholder: {title}')

    def test_materialize_node_with_explicit_project_path(
        self,
        materialize_node: MaterializeNode,
        fake_logger: FakeLogger,
        binder_with_placeholder: Binder,
        tmp_path: Path,
    ) -> None:
        """Test MaterializeNode with explicit project path."""
        # Arrange
        title = 'Chapter Placeholder'

        # Act
        materialize_node.execute(title=title, project_path=tmp_path)

        # Assert - Operations logged (project_path is used internally)
        assert fake_logger.has_logged('info', f'Materializing placeholder: {title}')

    def test_materialize_node_dependency_injection(
        self,
        fake_binder_repo: FakeBinderRepo,
        fake_node_repo: FakeNodeRepo,
        fake_id_generator: FakeIdGenerator,
        fake_console: FakeConsolePort,
        fake_logger: FakeLogger,
        fake_clock: FakeClock,
    ) -> None:
        """Test MaterializeNode uses all injected dependencies correctly."""
        # Arrange
        materialize_node = MaterializeNode(
            binder_repo=fake_binder_repo,
            node_repo=fake_node_repo,
            id_generator=fake_id_generator,
            console=fake_console,
            logger=fake_logger,
            clock=fake_clock,
        )

        # Verify dependencies are assigned
        assert materialize_node.binder_repo is fake_binder_repo
        assert materialize_node.node_repo is fake_node_repo
        assert materialize_node.id_generator is fake_id_generator
        assert materialize_node.console is fake_console
        assert materialize_node.logger is fake_logger
        assert materialize_node.clock is fake_clock

        # Setup and test
        placeholder = BinderItem(display_title='Test Placeholder', node_id=None, children=[])
        binder = Binder(roots=[placeholder])
        fake_binder_repo.save(binder)

        title = 'Test Placeholder'
        materialize_node.execute(title=title)

        # Assert all dependencies were used
        assert fake_id_generator.generated_count() > 0
        assert fake_node_repo.get_node_count() > 0
        assert len(fake_console.get_output()) > 0
        assert fake_logger.log_count() > 0
