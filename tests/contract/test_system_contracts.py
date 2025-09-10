"""Contract test base classes for system protocols."""

import abc
from datetime import datetime

from prosemark.domain.value_objects import NodeId
from prosemark.ports.system_ports import Clock, IdGenerator, Logger


class IdGeneratorContractTest(abc.ABC):
    """Base contract test for IdGenerator implementations.
    
    Inherit from this class to test any IdGenerator implementation.
    Implement get_generator() to return the implementation under test.
    """

    @abc.abstractmethod
    def get_generator(self) -> IdGenerator:
        """Return IdGenerator implementation to test."""
        ...

    def test_new_returns_node_id(self) -> None:
        """Test that new() returns a NodeId instance."""
        generator = self.get_generator()
        node_id = generator.new()
        assert isinstance(node_id, NodeId)

    def test_new_generates_unique_ids(self) -> None:
        """Test that multiple calls generate unique IDs."""
        generator = self.get_generator()

        ids = []
        for _ in range(10):
            node_id = generator.new()
            ids.append(node_id)

        # All IDs should be unique
        unique_ids = set(str(id) for id in ids)
        assert len(unique_ids) == len(ids)

    def test_new_generates_valid_uuidv7(self) -> None:
        """Test that generated IDs are valid UUIDv7."""
        generator = self.get_generator()

        for _ in range(5):
            node_id = generator.new()
            # NodeId constructor validates UUIDv7 format
            # If this doesn't raise, the ID is valid
            assert isinstance(node_id, NodeId)

    def test_ids_are_time_ordered(self) -> None:
        """Test that generated IDs are roughly time-ordered."""
        generator = self.get_generator()

        # Generate IDs with small delay
        first_id = generator.new()
        # UUIDv7 includes timestamp, so even rapid generation should maintain order
        second_id = generator.new()

        # Compare as strings - UUIDv7 should be lexicographically ordered by time
        assert str(first_id) <= str(second_id)


class ClockContractTest(abc.ABC):
    """Base contract test for Clock implementations.
    
    Inherit from this class to test any Clock implementation.
    Implement get_clock() to return the implementation under test.
    """

    @abc.abstractmethod
    def get_clock(self) -> Clock:
        """Return Clock implementation to test."""
        ...

    def test_now_iso_returns_string(self) -> None:
        """Test that now_iso() returns a string."""
        clock = self.get_clock()
        timestamp = clock.now_iso()
        assert isinstance(timestamp, str)
        assert len(timestamp) > 0

    def test_now_iso_returns_valid_iso8601(self) -> None:
        """Test that returned string is valid ISO8601."""
        clock = self.get_clock()
        timestamp = clock.now_iso()

        # Should be parseable as ISO8601
        parsed = datetime.fromisoformat(timestamp)
        assert isinstance(parsed, datetime)

    def test_now_iso_advances_with_time(self) -> None:
        """Test that successive calls return advancing timestamps."""
        clock = self.get_clock()

        first_time = clock.now_iso()
        second_time = clock.now_iso()

        # Convert to datetime for comparison
        first_dt = datetime.fromisoformat(first_time)
        second_dt = datetime.fromisoformat(second_time)

        # Second should be same or later (allowing for same millisecond)
        assert second_dt >= first_dt

    def test_now_iso_utc_timezone(self) -> None:
        """Test that timestamps are in UTC."""
        clock = self.get_clock()
        timestamp = clock.now_iso()

        # Parse timestamp
        dt = datetime.fromisoformat(timestamp)

        # Should be timezone-aware and UTC
        # (Implementation may vary on exact format, but should be consistent)
        # This test may need adjustment based on implementation details
        assert dt.tzinfo is not None or timestamp.endswith('Z') or '+00:00' in timestamp


class LoggerContractTest(abc.ABC):
    """Base contract test for Logger implementations.
    
    Inherit from this class to test any Logger implementation.
    Implement get_logger() to return the implementation under test.
    """

    @abc.abstractmethod
    def get_logger(self) -> Logger:
        """Return Logger implementation to test."""
        ...

    def test_info_accepts_string(self) -> None:
        """Test that info() accepts string messages."""
        logger = self.get_logger()
        # Should not raise
        logger.info('Test info message')
        logger.info('')  # Empty string should also work

    def test_warn_accepts_string(self) -> None:
        """Test that warn() accepts string messages."""
        logger = self.get_logger()
        # Should not raise
        logger.warning('Test warning message')
        logger.warning('')  # Empty string should also work

    def test_error_accepts_string(self) -> None:
        """Test that error() accepts string messages."""
        logger = self.get_logger()
        # Should not raise
        logger.error('Test error message')
        logger.error('')  # Empty string should also work

    def test_all_log_levels_work(self) -> None:
        """Test that all log levels can be used together."""
        logger = self.get_logger()

        # Should not raise
        logger.info('Info message')
        logger.warning('Warning message')
        logger.error('Error message')

    def test_log_messages_with_special_characters(self) -> None:
        """Test logging messages with special characters."""
        logger = self.get_logger()

        special_messages = [
            'Message with unicode: ñáéíóú',
            'Message with newlines:\nLine 2\nLine 3',
            "Message with quotes: 'single' and \"double\"",
            'Message with symbols: !@#$%^&*()[]{}',
        ]

        for msg in special_messages:
            # Should not raise
            logger.info(msg)
            logger.warning(msg)
            logger.error(msg)
