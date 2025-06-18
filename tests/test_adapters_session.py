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

    @patch('prosemark.adapters.session.FreezableWritingSession')
    def test_start_freewrite_session_success(
        self, mock_session: MagicMock, service: SessionService, repository: ProjectRepository
    ) -> None:
        """Test starting a freewrite session successfully."""
        # Mock load_node_content to simulate no existing content (new freewrite)
        repository.load_node_content = MagicMock()  # type: ignore[method-assign]
        repository.save_node = MagicMock()  # type: ignore[method-assign]

        # Mock the session instance
        mock_session_instance = MagicMock()
        mock_session.return_value = mock_session_instance

        success, message = service.start_freewrite_session(
            word_goal=100,
            time_limit=30,
            timer_mode='visible',
            stats_mode='detailed',
            no_prompt=True,
            date_str='2025-06-17',
            suffix='morning',
        )

        assert success
        assert 'completed successfully' in message[0]
        mock_session.assert_called_once()
        mock_session_instance.run.assert_called_once()
        repository.save_node.assert_called_once()

    @patch('prosemark.adapters.session.FreezableWritingSession')
    def test_start_freewrite_session_existing_node(
        self, mock_session: MagicMock, service: SessionService, repository: ProjectRepository
    ) -> None:
        """Test starting a freewrite session with an existing node."""

        # Mock load_node_content to simulate existing content being found
        def mock_load_node_content(node: Node) -> None:
            # Simulate loading existing freewrite content
            node.text = 'Existing content\n\n## Session 1 - June 17, 2025 08:30\n\nSome existing text.'
            node.metadata = {
                'type': 'freewrite',
                'date': '2025-06-17',
                'created': '2025-06-17T08:30:00.000000+00:00',
                'session_history': [],
            }

        repository.load_node_content = MagicMock(side_effect=mock_load_node_content)  # type: ignore[method-assign]

        # Mock the session instance
        mock_session_instance = MagicMock()
        mock_session.return_value = mock_session_instance

        success, message = service.start_freewrite_session(no_prompt=True)

        assert success
        assert 'completed successfully' in message[0]
        mock_session.assert_called_once()
        mock_session_instance.run.assert_called_once()

        # Verify that load_node_content was called to check for existing content
        repository.load_node_content.assert_called_once()

        # Verify the node passed to load_node_content has the expected ID
        call_args = repository.load_node_content.call_args[0]
        loaded_node = call_args[0]
        assert loaded_node.id.endswith('0000 daily')  # Today's date + suffix

    @patch('prosemark.adapters.session.FreezableWritingSession')
    def test_start_freewrite_session_invalid_date(
        self, mock_session: MagicMock, service: SessionService, repository: ProjectRepository
    ) -> None:
        """Test starting a freewrite session with invalid date."""
        success, message = service.start_freewrite_session(date_str='invalid-date')

        assert not success
        assert 'Invalid date format' in message[0]
        mock_session.assert_not_called()

    @patch('prosemark.adapters.session.FreezableWritingSession')
    def test_start_freewrite_session_exception(
        self, mock_session: MagicMock, service: SessionService, repository: ProjectRepository
    ) -> None:
        """Test handling exceptions during freewrite session."""
        # Mock load_node_content to simulate no existing content (new freewrite)
        repository.load_node_content = MagicMock()  # type: ignore[method-assign]
        repository.save_node = MagicMock()  # type: ignore[method-assign]

        # Mock the session instance to raise an exception
        mock_session_instance = MagicMock()
        mock_session_instance.run.side_effect = RuntimeError('Freewrite error')
        mock_session.return_value = mock_session_instance

        success, message = service.start_freewrite_session()

        assert not success
        assert 'error' in message[0]
        mock_session.assert_called_once()
        mock_session_instance.run.assert_called_once()

    def test_is_continuation_session_logic(self, service: SessionService) -> None:
        """Test the _is_continuation_session method directly."""
        from prosemark.domain.nodes import Node

        # Test 1: Empty node should not be continuation
        empty_node = Node(id='test1', title='Test', text='')
        assert not service._is_continuation_session(empty_node)  # noqa: SLF001

        # Test 2: Node with only whitespace should not be continuation
        whitespace_node = Node(id='test2', title='Test', text='  \n\n  ')
        assert not service._is_continuation_session(whitespace_node)  # noqa: SLF001

        # Test 3: Node with session header only should NOT be continuation (reuse the empty session)
        header_node = Node(id='test3', title='Test', text='## Session 1 - June 18, 2025 10:30\n\n')
        assert not service._is_continuation_session(header_node)  # noqa: SLF001

        # Test 4: Node with session header and content should be continuation
        content_node = Node(id='test4', title='Test', text='## Session 1 - June 18, 2025 10:30\n\nSome writing here.')
        assert service._is_continuation_session(content_node)  # noqa: SLF001

        # Test 5: Node with first session content + empty second session should NOT be continuation
        empty_second_session = Node(
            id='test5a',
            title='Test',
            text='## Session 1 - June 18, 2025 10:30\n\nFirst session.\n\n## Session 2 - June 18, 2025 14:30\n\n',
        )
        assert not service._is_continuation_session(empty_second_session)  # noqa: SLF001

        # Test 6: Node with multiple sessions with content should be continuation
        multi_session_node = Node(
            id='test5',
            title='Test',
            text='## Session 1 - June 18, 2025 10:30\n\nFirst session.\n\n## Session 2 - June 18, 2025 14:30\n\nSecond session.',
        )
        assert service._is_continuation_session(multi_session_node)  # noqa: SLF001

        # Test 7: Node with other content but no session header should not be continuation
        other_content_node = Node(id='test6', title='Test', text='Some other content\n\n# A heading\n\nMore text.')
        assert not service._is_continuation_session(other_content_node)  # noqa: SLF001

    def test_freewrite_session_numbering_behavior(self, service: SessionService, repository: ProjectRepository) -> None:
        """Test that freewrite sessions are numbered correctly in continuation scenarios."""
        from prosemark.domain.nodes import Node

        # Simulate the scenario that was problematic:
        # 1. First session creates "Session 1"
        # 2. Second session should create "Session 2", not overwrite

        # Create a node that would be created after first freewrite session
        first_session_node = Node(
            id='202506180000 daily',
            title='Freewrite Daily - June 18, 2025',
            text='## Session 1 - June 18, 2025 10:30\n\nSome writing from first session.',
            metadata={'type': 'freewrite', 'date': '2025-06-18'},
        )

        # Check that this is detected as a continuation (since it has content after Session 1)
        assert service._is_continuation_session(first_session_node)  # noqa: SLF001

        # Now simulate what happens when we create a FreezableWritingSession for continuation
        # The session should append a new header, not overwrite
        from prosemark.adapters.session import FreezableWritingSession

        # Create a mock repository for this test
        def mock_save_node(_: Node) -> None:
            pass

        repository.save_node = mock_save_node  # type: ignore[assignment]

        # Create the continuation session
        session = FreezableWritingSession(
            node=first_session_node,
            repository=repository,
            word_goal=None,
            time_limit=None,
            timer_mode='visible',
            stats_mode='minimal',
            no_prompt=True,
            is_continuation=True,
        )

        # Check that the node text now contains both sessions
        expected_session_2_header = '## Session 2 - June 18, 2025'
        assert 'Session 1' in first_session_node.text
        assert expected_session_2_header in first_session_node.text
        assert 'Some writing from first session.' in first_session_node.text

        # Verify that the committed_lines contain all the content including both session headers
        assert len(session.committed_lines) > 2  # Should have multiple lines
        session_headers_in_committed = [line for line in session.committed_lines if line.startswith('## Session ')]
        assert len(session_headers_in_committed) == 2  # Should have both Session 1 and Session 2 headers


# Note: We can't easily test WritingSession directly because it uses prompt_toolkit's
# interactive features. We would need to mock the Application and other components.
# In a real project, we would refactor to make it more testable or use integration tests.
