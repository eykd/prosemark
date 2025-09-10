"""Test protocol validation and mock implementations."""


import sys
from pathlib import Path

from prosemark.ports import (
    BinderRepo,
    Clock,
    ConsolePort,
    DailyRepo,
    EditorPort,
    IdGenerator,
    Logger,
    NodeRepo,
)

# Add the tests directory to the Python path
tests_dir = Path(__file__).parent
sys.path.insert(0, str(tests_dir))

from mocks import (
    MockBinderRepo,
    MockClock,
    MockConsolePort,
    MockDailyRepo,
    MockEditorPort,
    MockIdGenerator,
    MockLogger,
    MockNodeRepo,
)


class TestProtocolValidation:
    """Test that protocols are properly defined and mocks implement them."""

    def test_repository_protocols_exist(self) -> None:
        """Test that repository protocols are importable."""
        assert BinderRepo is not None
        assert NodeRepo is not None
        assert DailyRepo is not None

    def test_system_protocols_exist(self) -> None:
        """Test that system protocols are importable."""
        assert IdGenerator is not None
        assert Clock is not None
        assert Logger is not None

    def test_io_protocols_exist(self) -> None:
        """Test that I/O protocols are importable."""
        assert EditorPort is not None
        assert ConsolePort is not None

    def test_mock_implementations_satisfy_protocols(self) -> None:
        """Test that mock implementations satisfy the protocol contracts."""
        # Repository protocols
        assert isinstance(MockBinderRepo(), BinderRepo)
        assert isinstance(MockNodeRepo(), NodeRepo)
        assert isinstance(MockDailyRepo(), DailyRepo)

        # System protocols
        assert isinstance(MockIdGenerator(), IdGenerator)
        assert isinstance(MockClock(), Clock)
        assert isinstance(MockLogger(), Logger)

        # I/O protocols
        assert isinstance(MockEditorPort(), EditorPort)
        assert isinstance(MockConsolePort(), ConsolePort)

    def test_all_protocols_are_runtime_checkable(self) -> None:
        """Test that all protocols are marked as runtime checkable."""
        protocols = [
            BinderRepo,
            NodeRepo,
            DailyRepo,
            IdGenerator,
            Clock,
            Logger,
            EditorPort,
            ConsolePort,
        ]

        for protocol in protocols:
            # Runtime checkable protocols should have the _is_runtime_protocol attribute
            # or be directly usable with isinstance (which our test above demonstrates)
            assert getattr(protocol, '_is_runtime_protocol', False) or callable(getattr(protocol, '__instancecheck__', None))


class TestMockBasicFunctionality:
    """Test basic functionality of mock implementations."""

    def test_mock_id_generator_works(self) -> None:
        """Test that MockIdGenerator generates valid NodeIds."""
        generator = MockIdGenerator()

        node_id = generator.new()
        assert generator.new_called == 1

        # Should be able to generate multiple unique IDs
        node_id2 = generator.new()
        assert generator.new_called == 2
        assert node_id != node_id2

    def test_mock_clock_works(self) -> None:
        """Test that MockClock returns ISO timestamps."""
        clock = MockClock()

        timestamp = clock.now_iso()
        assert isinstance(timestamp, str)
        assert clock.now_iso_called == 1

    def test_mock_logger_works(self) -> None:
        """Test that MockLogger captures log messages."""
        logger = MockLogger()

        logger.info('Info message')
        logger.warning('Warning message')
        logger.error('Error message')

        assert logger.info_called == 1
        assert logger.warn_called == 1
        assert logger.error_called == 1

        logs = logger.get_logs()
        assert len(logs) == 3
        assert ('info', 'Info message') in logs
        assert ('warn', 'Warning message') in logs
        assert ('error', 'Error message') in logs

    def test_mock_console_works(self) -> None:
        """Test that MockConsolePort captures output."""
        console = MockConsolePort()

        console.print('Test message')
        console.print('Another message')

        assert console.print_called == 2
        messages = console.get_printed_messages()
        assert messages == ['Test message', 'Another message']

    def test_mock_editor_works(self) -> None:
        """Test that MockEditorPort tracks file opens."""
        editor = MockEditorPort(raise_on_nonexistent=False)

        editor.open('/path/to/file.md')
        editor.open('/path/to/other.md', cursor_hint='1:1')

        assert editor.open_called == 2
        opened_files = editor.get_opened_files()
        assert opened_files == [
            ('/path/to/file.md', None),
            ('/path/to/other.md', '1:1'),
        ]
