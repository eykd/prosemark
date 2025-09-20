"""Tests for EditPart use case interactor."""

import pytest

from prosemark.adapters.fake_logger import FakeLogger
from prosemark.adapters.fake_node_repo import FakeNodeRepo
from prosemark.adapters.fake_storage import FakeBinderRepo
from prosemark.app.use_cases import EditPart
from prosemark.domain.models import Binder, BinderItem, NodeId
from prosemark.exceptions import NodeNotFoundError


class TestEditPart:
    """Test suite for EditPart use case interactor."""

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
    def sample_node_id(self) -> NodeId:
        """Sample NodeId for testing."""
        return NodeId('0192f0c1-2345-7123-8abc-def012345678')

    @pytest.fixture
    def binder_with_node(self, sample_node_id: NodeId) -> Binder:
        """Binder containing a sample node."""
        item = BinderItem(id_=sample_node_id, display_title='Test Node', children=[])
        return Binder(roots=[item])

    @pytest.fixture
    def empty_binder(self) -> Binder:
        """Empty binder with no nodes."""
        return Binder(roots=[])

    def test_execute_opens_draft_part_successfully(
        self,
        fake_binder_repo: FakeBinderRepo,
        fake_node_repo: FakeNodeRepo,
        fake_logger: FakeLogger,
        binder_with_node: Binder,
        sample_node_id: NodeId,
    ) -> None:
        """Test that EditPart successfully opens draft part."""
        # Arrange
        fake_binder_repo.set_binder(binder_with_node)
        fake_node_repo.create(sample_node_id, 'Test Node', 'Test synopsis')
        edit_part = EditPart(fake_binder_repo, fake_node_repo, fake_logger)

        # Act
        edit_part.execute(sample_node_id, 'draft')

        # Assert
        assert fake_node_repo.open_in_editor_calls == [(sample_node_id, 'draft')]
        assert len(fake_logger.info_messages) == 2
        assert 'Starting edit operation' in fake_logger.info_messages[0]
        assert 'Edit operation completed successfully' in fake_logger.info_messages[1]

    def test_execute_opens_notes_part_successfully(
        self,
        fake_binder_repo: FakeBinderRepo,
        fake_node_repo: FakeNodeRepo,
        fake_logger: FakeLogger,
        binder_with_node: Binder,
        sample_node_id: NodeId,
    ) -> None:
        """Test that EditPart successfully opens notes part."""
        # Arrange
        fake_binder_repo.set_binder(binder_with_node)
        fake_node_repo.create(sample_node_id, 'Test Node', 'Test synopsis')
        edit_part = EditPart(fake_binder_repo, fake_node_repo, fake_logger)

        # Act
        edit_part.execute(sample_node_id, 'notes')

        # Assert
        assert fake_node_repo.open_in_editor_calls == [(sample_node_id, 'notes')]
        assert len(fake_logger.info_messages) == 2
        assert 'Starting edit operation' in fake_logger.info_messages[0]
        assert 'Edit operation completed successfully' in fake_logger.info_messages[1]

    def test_execute_opens_synopsis_part_successfully(
        self,
        fake_binder_repo: FakeBinderRepo,
        fake_node_repo: FakeNodeRepo,
        fake_logger: FakeLogger,
        binder_with_node: Binder,
        sample_node_id: NodeId,
    ) -> None:
        """Test that EditPart successfully opens synopsis part."""
        # Arrange
        fake_binder_repo.set_binder(binder_with_node)
        fake_node_repo.create(sample_node_id, 'Test Node', 'Test synopsis')
        edit_part = EditPart(fake_binder_repo, fake_node_repo, fake_logger)

        # Act
        edit_part.execute(sample_node_id, 'synopsis')

        # Assert
        assert fake_node_repo.open_in_editor_calls == [(sample_node_id, 'synopsis')]
        assert len(fake_logger.info_messages) == 2
        assert 'Starting edit operation' in fake_logger.info_messages[0]
        assert 'Edit operation completed successfully' in fake_logger.info_messages[1]

    def test_execute_raises_error_when_node_not_found(
        self,
        fake_binder_repo: FakeBinderRepo,
        fake_node_repo: FakeNodeRepo,
        fake_logger: FakeLogger,
        empty_binder: Binder,
        sample_node_id: NodeId,
    ) -> None:
        """Test that EditPart raises NodeNotFoundError when node doesn't exist."""
        # Arrange
        fake_binder_repo.set_binder(empty_binder)
        edit_part = EditPart(fake_binder_repo, fake_node_repo, fake_logger)

        # Act & Assert
        with pytest.raises(NodeNotFoundError, match='Node not found in binder'):
            edit_part.execute(sample_node_id, 'draft')

        # Assert no editor calls were made
        assert fake_node_repo.open_in_editor_calls == []
        assert len(fake_logger.error_messages) == 1
        assert 'Node not found in binder' in fake_logger.error_messages[0]

    def test_execute_raises_error_for_invalid_part(
        self,
        fake_binder_repo: FakeBinderRepo,
        fake_node_repo: FakeNodeRepo,
        fake_logger: FakeLogger,
        binder_with_node: Binder,
        sample_node_id: NodeId,
    ) -> None:
        """Test that EditPart raises ValueError for invalid part."""
        # Arrange
        fake_binder_repo.set_binder(binder_with_node)
        fake_node_repo.create(sample_node_id, 'Test Node', 'Test synopsis')
        edit_part = EditPart(fake_binder_repo, fake_node_repo, fake_logger)

        # Act & Assert
        with pytest.raises(ValueError, match='Invalid part: invalid_part'):
            edit_part.execute(sample_node_id, 'invalid_part')

        # Assert no editor calls were made
        assert fake_node_repo.open_in_editor_calls == []
        assert len(fake_logger.error_messages) == 1
        assert 'Invalid part specified' in fake_logger.error_messages[0]

    def test_execute_validates_all_valid_parts(
        self,
        fake_binder_repo: FakeBinderRepo,
        fake_node_repo: FakeNodeRepo,
        fake_logger: FakeLogger,
        binder_with_node: Binder,
        sample_node_id: NodeId,
    ) -> None:
        """Test that all valid parts are accepted."""
        # Arrange
        fake_binder_repo.set_binder(binder_with_node)
        fake_node_repo.create(sample_node_id, 'Test Node', 'Test synopsis')
        edit_part = EditPart(fake_binder_repo, fake_node_repo, fake_logger)

        valid_parts = ['draft', 'notes', 'synopsis']

        # Act & Assert
        for part in valid_parts:
            # Reset for each test
            fake_node_repo.open_in_editor_calls = []
            fake_logger.clear()

            # Test the part
            edit_part.execute(sample_node_id, part)
            assert fake_node_repo.open_in_editor_calls == [(sample_node_id, part)]

    def test_execute_logs_validation_success(
        self,
        fake_binder_repo: FakeBinderRepo,
        fake_node_repo: FakeNodeRepo,
        fake_logger: FakeLogger,
        binder_with_node: Binder,
        sample_node_id: NodeId,
    ) -> None:
        """Test that EditPart logs validation success."""
        # Arrange
        fake_binder_repo.set_binder(binder_with_node)
        fake_node_repo.create(sample_node_id, 'Test Node', 'Test synopsis')
        edit_part = EditPart(fake_binder_repo, fake_node_repo, fake_logger)

        # Act
        edit_part.execute(sample_node_id, 'draft')

        # Assert
        debug_messages = fake_logger.debug_messages
        assert len(debug_messages) == 2
        assert 'Validation passed: node exists and part is valid' in debug_messages[0]
        assert 'Opening draft part of node' in debug_messages[1]

    def test_execute_works_with_nested_node(
        self,
        fake_binder_repo: FakeBinderRepo,
        fake_node_repo: FakeNodeRepo,
        fake_logger: FakeLogger,
        sample_node_id: NodeId,
    ) -> None:
        """Test that EditPart works with nested nodes in binder."""
        # Arrange - Create binder with nested structure
        child_id = NodeId('0192f0c1-2345-7123-8abc-def012345679')
        child_item = BinderItem(id_=child_id, display_title='Child Node', children=[])
        parent_item = BinderItem(id_=sample_node_id, display_title='Parent Node', children=[child_item])
        binder = Binder(roots=[parent_item])

        fake_binder_repo.set_binder(binder)
        fake_node_repo.create(sample_node_id, 'Parent Node', 'Parent synopsis')
        fake_node_repo.create(child_id, 'Child Node', 'Child synopsis')
        edit_part = EditPart(fake_binder_repo, fake_node_repo, fake_logger)

        # Act - Edit the nested child
        edit_part.execute(child_id, 'notes')

        # Assert
        assert fake_node_repo.open_in_editor_calls == [(child_id, 'notes')]
        assert 'Edit operation completed successfully' in fake_logger.info_messages[-1]

    def test_execute_propagates_node_repo_exceptions(
        self,
        fake_binder_repo: FakeBinderRepo,
        fake_node_repo: FakeNodeRepo,
        fake_logger: FakeLogger,
        binder_with_node: Binder,
        sample_node_id: NodeId,
    ) -> None:
        """Test that EditPart propagates exceptions from NodeRepo."""
        # Arrange
        fake_binder_repo.set_binder(binder_with_node)
        fake_node_repo.create(sample_node_id, 'Test Node', 'Test synopsis')
        fake_node_repo.set_open_in_editor_exception(RuntimeError('Editor launch failed'))
        edit_part = EditPart(fake_binder_repo, fake_node_repo, fake_logger)

        # Act & Assert
        with pytest.raises(RuntimeError, match='Editor launch failed'):
            edit_part.execute(sample_node_id, 'draft')

        # Assert the editor was attempted to be called
        assert fake_node_repo.open_in_editor_calls == [(sample_node_id, 'draft')]
