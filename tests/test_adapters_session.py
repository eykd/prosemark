"""Tests for the session adapter."""

from datetime import UTC, datetime, timedelta
from unittest.mock import MagicMock, patch

import pytest

from prosemark.adapters.session import SessionService, SessionStats
from prosemark.domain.nodes import Node
from prosemark.repositories.project import ProjectRepository
from prosemark.storages.inmemory import InMemoryNodeStorage


class TestSessionStats:
    """Tests for the SessionStats class."""

    def test_elapsed_seconds(self) -> None:
        """Test calculating elapsed seconds."""
        start_time = datetime.now(UTC) - timedelta(seconds=30)
        stats = SessionStats(
            start_time=start_time,
            end_time=None,
            initial_word_count=100,
            final_word_count=150,
            word_goal=200,
            time_limit_minutes=10,
        )

        # Should be approximately 30 seconds
        assert 29 <= stats.elapsed_seconds <= 31

    def test_elapsed_minutes(self) -> None:
        """Test calculating elapsed minutes."""
        start_time = datetime.now(UTC) - timedelta(minutes=2)
        stats = SessionStats(
            start_time=start_time,
            end_time=None,
            initial_word_count=100,
            final_word_count=150,
            word_goal=200,
            time_limit_minutes=10,
        )

        # Should be approximately 2 minutes
        assert 1.9 <= stats.elapsed_minutes <= 2.1

    def test_words_written(self) -> None:
        """Test calculating words written."""
        stats = SessionStats(
            start_time=datetime.now(UTC),
            end_time=None,
            initial_word_count=100,
            final_word_count=150,
            word_goal=200,
            time_limit_minutes=10,
        )

        assert stats.words_written == 50

    def test_words_per_minute(self) -> None:
        """Test calculating words per minute."""
        start_time = datetime.now(UTC) - timedelta(minutes=2)
        stats = SessionStats(
            start_time=start_time,
            end_time=None,
            initial_word_count=100,
            final_word_count=150,
            word_goal=200,
            time_limit_minutes=10,
        )

        # Should be approximately 25 wpm (50 words in 2 minutes)
        assert 24 <= stats.words_per_minute <= 26

    def test_words_per_minute_zero_elapsed(self) -> None:
        """Test words per minute with zero elapsed time."""
        now = datetime(2024, 1, 1, 0, 0, 0, tzinfo=UTC)
        stats = SessionStats(
            start_time=now,
            end_time=now,
            initial_word_count=100,
            final_word_count=150,
            word_goal=200,
            time_limit_minutes=10,
        )
        assert stats.words_per_minute == 0.0

    def test_goal_progress(self) -> None:
        """Test calculating goal progress."""
        stats = SessionStats(
            start_time=datetime.now(UTC),
            end_time=None,
            initial_word_count=100,
            final_word_count=150,
            word_goal=200,
            time_limit_minutes=10,
        )

        # 50 words out of 200 goal = 25%
        assert stats.goal_progress == 25.0

    def test_goal_progress_no_goal(self) -> None:
        """Test goal progress with no goal set."""
        stats = SessionStats(
            start_time=datetime.now(UTC),
            end_time=None,
            initial_word_count=100,
            final_word_count=150,
            word_goal=None,
            time_limit_minutes=10,
        )

        assert stats.goal_progress == 0.0

    def test_time_progress(self) -> None:
        """Test calculating time progress."""
        start_time = datetime.now(UTC) - timedelta(minutes=5)
        stats = SessionStats(
            start_time=start_time,
            end_time=None,
            initial_word_count=100,
            final_word_count=150,
            word_goal=200,
            time_limit_minutes=10,
        )

        # 5 minutes out of 10 = 50%
        assert 49 <= stats.time_progress <= 51

    def test_time_progress_no_limit(self) -> None:
        """Test time progress with no time limit."""
        stats = SessionStats(
            start_time=datetime.now(UTC),
            end_time=None,
            initial_word_count=100,
            final_word_count=150,
            word_goal=200,
            time_limit_minutes=None,
        )

        assert stats.time_progress == 0.0

    def test_time_remaining_minutes(self) -> None:
        """Test calculating remaining time."""
        start_time = datetime.now(UTC) - timedelta(minutes=3)
        stats = SessionStats(
            start_time=start_time,
            end_time=None,
            initial_word_count=100,
            final_word_count=150,
            word_goal=200,
            time_limit_minutes=10,
        )

        # 10 minute limit - 3 minutes elapsed = 7 minutes remaining
        assert stats.time_remaining_minutes is not None
        assert 6.9 <= stats.time_remaining_minutes <= 7.1

    def test_time_remaining_minutes_no_limit(self) -> None:
        """Test remaining time with no time limit."""
        stats = SessionStats(
            start_time=datetime.now(UTC),
            end_time=None,
            initial_word_count=100,
            final_word_count=150,
            word_goal=None,
            time_limit_minutes=None,
        )

        assert stats.time_remaining_minutes is None

    def test_time_remaining_minutes_exceeded(self) -> None:
        """Test remaining time when time limit is exceeded."""
        start_time = datetime.now(UTC) - timedelta(minutes=15)
        stats = SessionStats(
            start_time=start_time,
            end_time=None,
            initial_word_count=100,
            final_word_count=150,
            word_goal=200,
            time_limit_minutes=10,
        )

        # Time limit exceeded, should return 0
        assert stats.time_remaining_minutes == 0.0


class TestSessionService:
    """Tests for the SessionService class."""

    @pytest.fixture
    def repository(self) -> ProjectRepository:
        """Create a project repository with a mock storage."""
        storage = InMemoryNodeStorage()
        return ProjectRepository(storage)

    @pytest.fixture
    def service(self, repository: ProjectRepository) -> SessionService:
        """Create a session service."""
        return SessionService(repository)

    @patch('prosemark.adapters.session.WritingSession')
    def test_start_session_node_not_found(
        self, mock_session: MagicMock, service: SessionService, repository: ProjectRepository
    ) -> None:
        """Test starting a session with a non-existent node."""
        # Mock the project to return None for get_node_by_id
        mock_project = MagicMock()
        mock_project.get_node_by_id.return_value = None
        repository.load_project = MagicMock()  # type: ignore[method-assign]
        repository.load_project.return_value = mock_project

        success, message = service.start_session('nonexistent')

        assert not success
        assert 'not found' in message[0]
        mock_session.assert_not_called()

    @patch('prosemark.adapters.session.WritingSession')
    def test_start_session_success(
        self, mock_session: MagicMock, service: SessionService, repository: ProjectRepository
    ) -> None:
        """Test starting a session successfully."""
        # Mock the project and node
        mock_node = MagicMock(spec=Node)
        mock_node.id = 'node123'  # Ensure mock_node has an 'id' attribute
        mock_project = MagicMock()
        mock_project.get_node_by_id.return_value = mock_node
        repository.load_project = MagicMock()  # type: ignore[method-assign]
        repository.load_project.return_value = mock_project

        # Mock the session instance
        mock_session_instance = MagicMock()
        mock_session.return_value = mock_session_instance

        success, message = service.start_session(
            'node123',
            word_goal=100,
            time_limit=30,
            timer_mode='visible',
            stats_mode='detailed',
            no_prompt=True,
        )

        assert success
        assert 'completed successfully' in message[0]
        mock_session.assert_called_once_with(
            node=mock_node,
            repository=repository,
            word_goal=100,
            time_limit=30,
            timer_mode='visible',
            stats_mode='detailed',
            no_prompt=True,
        )
        mock_session_instance.run.assert_called_once()

    @patch('prosemark.adapters.session.WritingSession')
    def test_start_session_exception(
        self, mock_session: MagicMock, service: SessionService, repository: ProjectRepository
    ) -> None:
        """Test handling exceptions during session."""
        # Mock the project and node
        mock_node = MagicMock(spec=Node)
        mock_node.id = 'node123'  # Ensure mock_node has an 'id' attribute
        mock_project = MagicMock()
        mock_project.get_node_by_id.return_value = mock_node
        repository.load_project = MagicMock()  # type: ignore[method-assign]
        repository.load_project.return_value = mock_project

        # Mock the session instance to raise an exception
        mock_session_instance = MagicMock()
        mock_session_instance.run.side_effect = RuntimeError('Test error')
        mock_session.return_value = mock_session_instance

        success, message = service.start_session('node123')

        assert not success
        assert 'error' in message[0]
        mock_session.assert_called_once()
        mock_session_instance.run.assert_called_once()

    @patch('prosemark.adapters.session.WritingSession')
    def test_start_card_session_node_not_found(
        self, mock_session: MagicMock, service: SessionService, repository: ProjectRepository
    ) -> None:
        """Test starting a card session with a non-existent node."""
        mock_project = MagicMock()
        mock_project.get_node_by_id.return_value = None
        repository.load_project = MagicMock()  # type: ignore[method-assign]
        repository.load_project.return_value = mock_project

        success, message = service.start_card_session('nonexistent')

        assert not success
        assert 'not found' in message[0]
        mock_session.assert_not_called()

    @patch('prosemark.adapters.session.WritingSession')
    def test_start_card_session_success(
        self, mock_session: MagicMock, service: SessionService, repository: ProjectRepository
    ) -> None:
        """Test starting a card session successfully."""
        # Mock the project and node
        mock_node = MagicMock(spec=Node)
        mock_node.id = 'node123'
        mock_node.title = 'Node Title'
        mock_node.card = 'Card content'
        mock_node.metadata = {'card': {'foo': 'bar'}}
        mock_project = MagicMock()
        mock_project.get_node_by_id.return_value = mock_node
        repository.load_project = MagicMock()  # type: ignore[method-assign]
        repository.load_project.return_value = mock_project
        repository.save_node = MagicMock()  # type: ignore[method-assign]

        # Mock the session instance
        mock_session_instance = MagicMock()
        mock_session.return_value = mock_session_instance

        # Simulate card_node.text and card_node.metadata after session
        def run_side_effect() -> None:
            mock_session.call_args[1]['node'].text = 'Edited card content'
            mock_session.call_args[1]['node'].metadata = {'baz': 'qux'}

        mock_session_instance.run.side_effect = run_side_effect

        mock_node.metadata = {'card': {'foo': 'bar'}}
        mock_node.card = 'Card content'
        mock_node.text = ''
        mock_node.notes = ''

        success, message = service.start_card_session(
            'node123',
            word_goal=50,
            time_limit=10,
            timer_mode='alert',
            stats_mode='detailed',
            no_prompt=True,
        )

        assert success
        assert 'completed successfully' in message[0]
        mock_session.assert_called_once()
        mock_session_instance.run.assert_called_once()
        # Card and metadata should be updated
        assert mock_node.card == 'Edited card content'
        assert 'baz' in mock_node.metadata['card']
        repository.save_node.assert_called_once_with(mock_node)

    @patch('prosemark.adapters.session.WritingSession')
    def test_start_card_session_exception(
        self, mock_session: MagicMock, service: SessionService, repository: ProjectRepository
    ) -> None:
        """Test handling exceptions during card session."""
        mock_node = MagicMock(spec=Node)
        mock_node.id = 'node123'
        mock_node.title = 'Node Title'
        mock_node.card = 'Card content'
        mock_node.metadata = {'card': {}}
        mock_project = MagicMock()
        mock_project.get_node_by_id.return_value = mock_node
        repository.load_project = MagicMock()  # type: ignore[method-assign]
        repository.load_project.return_value = mock_project

        mock_session_instance = MagicMock()
        mock_session_instance.run.side_effect = RuntimeError('Card error')
        mock_session.return_value = mock_session_instance

        success, message = service.start_card_session('node123')

        assert not success
        assert 'error' in message[0]
        mock_session.assert_called_once()
        mock_session_instance.run.assert_called_once()


# Note: We can't easily test WritingSession directly because it uses prompt_toolkit's
# interactive features. We would need to mock the Application and other components.
# In a real project, we would refactor to make it more testable or use integration tests.
