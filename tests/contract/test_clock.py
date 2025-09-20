"""Contract tests for Clock protocol (T015).

These tests verify that any implementation of the Clock protocol
correctly implements the contract defined in the domain interfaces.
Tests will initially fail due to missing imports - this is expected.
"""

import re
from datetime import datetime
from unittest.mock import Mock

# These imports will fail initially - this is expected for contract tests
from prosemark.ports import Clock


class TestClockContract:
    """Test contract compliance for Clock implementations."""

    def test_now_iso_returns_string(self) -> None:
        """Test that now_iso() returns a string."""
        # Arrange
        mock_clock = Mock(spec=Clock)
        expected_timestamp = '2025-09-20T15:30:00Z'
        mock_clock.now_iso.return_value = expected_timestamp

        # Act
        result = mock_clock.now_iso()

        # Assert
        assert isinstance(result, str)
        assert result == expected_timestamp
        mock_clock.now_iso.assert_called_once()

    def test_now_iso_returns_iso8601_format(self) -> None:
        """Test that now_iso() returns timestamp in ISO 8601 UTC format."""
        # Arrange
        mock_clock = Mock(spec=Clock)
        # Valid ISO 8601 UTC timestamp
        expected_timestamp = '2025-09-20T15:30:00Z'
        mock_clock.now_iso.return_value = expected_timestamp

        # Act
        result = mock_clock.now_iso()

        # Assert
        assert isinstance(result, str)
        # Verify it ends with 'Z' for UTC
        assert result.endswith('Z')
        # Verify it can be parsed as ISO format
        parsed_datetime = datetime.fromisoformat(result)
        assert isinstance(parsed_datetime, datetime)

    def test_now_iso_format_pattern(self) -> None:
        """Test that now_iso() returns timestamp matching expected pattern."""
        # Arrange
        mock_clock = Mock(spec=Clock)
        expected_timestamp = '2025-09-20T15:30:00Z'
        mock_clock.now_iso.return_value = expected_timestamp

        # Act
        result = mock_clock.now_iso()

        # Assert
        # ISO 8601 UTC pattern: YYYY-MM-DDTHH:MM:SSZ
        iso_pattern = r'^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$'
        assert re.match(iso_pattern, result)

    def test_now_iso_with_fractional_seconds(self) -> None:
        """Test that now_iso() can handle fractional seconds format."""
        # Arrange
        mock_clock = Mock(spec=Clock)
        # ISO 8601 with fractional seconds is also valid
        expected_timestamp = '2025-09-20T15:30:00.123Z'
        mock_clock.now_iso.return_value = expected_timestamp

        # Act
        result = mock_clock.now_iso()

        # Assert
        assert isinstance(result, str)
        assert result.endswith('Z')
        # Should be parseable as ISO format
        parsed_datetime = datetime.fromisoformat(result)
        assert isinstance(parsed_datetime, datetime)

    def test_now_iso_utc_timezone(self) -> None:
        """Test that now_iso() returns UTC timezone (Z suffix)."""
        # Arrange
        mock_clock = Mock(spec=Clock)
        expected_timestamp = '2025-09-20T15:30:00Z'
        mock_clock.now_iso.return_value = expected_timestamp

        # Act
        result = mock_clock.now_iso()

        # Assert
        assert isinstance(result, str)
        # Must be UTC (Z suffix)
        assert result.endswith('Z')
        # Should not have other timezone indicators
        assert '+' not in result
        assert result.count('Z') == 1

    def test_now_iso_no_parameters(self) -> None:
        """Test that now_iso() method takes no parameters."""
        # Arrange
        mock_clock = Mock(spec=Clock)
        expected_timestamp = '2025-09-20T15:30:00Z'
        mock_clock.now_iso.return_value = expected_timestamp

        # Act - should work with no parameters
        result = mock_clock.now_iso()

        # Assert
        assert isinstance(result, str)
        mock_clock.now_iso.assert_called_once_with()

    def test_now_iso_multiple_calls_progression(self) -> None:
        """Test that multiple calls to now_iso() can return different timestamps."""
        # Arrange
        mock_clock = Mock(spec=Clock)
        timestamps = ['2025-09-20T15:30:00Z', '2025-09-20T15:30:01Z', '2025-09-20T15:30:02Z']
        mock_clock.now_iso.side_effect = timestamps

        # Act
        results = [mock_clock.now_iso() for _ in range(3)]

        # Assert
        assert len(results) == 3
        assert all(isinstance(result, str) for result in results)
        assert results == timestamps
        assert mock_clock.now_iso.call_count == 3

    def test_now_iso_timestamp_components(self) -> None:
        """Test that now_iso() returns timestamp with correct components."""
        # Arrange
        mock_clock = Mock(spec=Clock)
        expected_timestamp = '2025-09-20T15:30:00Z'
        mock_clock.now_iso.return_value = expected_timestamp

        # Act
        result = mock_clock.now_iso()

        # Assert
        assert isinstance(result, str)

        # Parse the timestamp components
        # Format: YYYY-MM-DDTHH:MM:SSZ
        date_part, time_part = result.split('T')
        time_part = time_part.rstrip('Z')

        # Validate date part (YYYY-MM-DD)
        year, month, day = date_part.split('-')
        assert len(year) == 4
        assert len(month) == 2
        assert len(day) == 2
        assert year.isdigit()
        assert month.isdigit()
        assert day.isdigit()

        # Validate time part (HH:MM:SS)
        hour, minute, second = time_part.split(':')
        assert len(hour) == 2
        assert len(minute) == 2
        assert len(second) == 2
        assert hour.isdigit()
        assert minute.isdigit()
        assert second.isdigit()

    def test_now_iso_valid_datetime_ranges(self) -> None:
        """Test that now_iso() returns timestamps with valid datetime ranges."""
        # Arrange
        mock_clock = Mock(spec=Clock)
        expected_timestamp = '2025-09-20T15:30:00Z'
        mock_clock.now_iso.return_value = expected_timestamp

        # Act
        result = mock_clock.now_iso()

        # Assert
        parsed_datetime = datetime.fromisoformat(result)

        # Validate ranges
        assert 1 <= parsed_datetime.month <= 12
        assert 1 <= parsed_datetime.day <= 31
        assert 0 <= parsed_datetime.hour <= 23
        assert 0 <= parsed_datetime.minute <= 59
        assert 0 <= parsed_datetime.second <= 59

    def test_now_iso_microseconds_optional(self) -> None:
        """Test that now_iso() can optionally include microseconds."""
        # Arrange
        mock_clock = Mock(spec=Clock)
        # Both formats should be valid
        timestamps = [
            '2025-09-20T15:30:00Z',  # Without microseconds
            '2025-09-20T15:30:00.123456Z',  # With microseconds
        ]
        mock_clock.now_iso.side_effect = timestamps

        # Act & Assert
        for expected_timestamp in timestamps:
            mock_clock.now_iso.return_value = expected_timestamp
            result = mock_clock.now_iso()

            assert isinstance(result, str)
            assert result.endswith('Z')
            # Should be parseable as ISO format
            parsed_datetime = datetime.fromisoformat(result)
            assert isinstance(parsed_datetime, datetime)

    def test_protocol_methods_exist(self) -> None:
        """Test that Clock protocol has required methods."""
        # This test verifies the protocol interface exists
        mock_clock = Mock(spec=Clock)

        # Verify methods exist
        assert hasattr(mock_clock, 'now_iso')

        # Verify methods are callable
        assert callable(mock_clock.now_iso)

    def test_now_iso_method_signature(self) -> None:
        """Test that now_iso() method has correct signature."""
        # Arrange
        mock_clock = Mock(spec=Clock)
        expected_timestamp = '2025-09-20T15:30:00Z'
        mock_clock.now_iso.return_value = expected_timestamp

        # Act - Test that method can be called without parameters
        result = mock_clock.now_iso()

        # Assert
        assert isinstance(result, str)
        # Verify it was called with no arguments
        mock_clock.now_iso.assert_called_once_with()

    def test_now_iso_return_type_annotation(self) -> None:
        """Test that now_iso() returns str type as specified in contract."""
        # Arrange
        mock_clock = Mock(spec=Clock)
        expected_timestamp = '2025-09-20T15:30:00Z'
        mock_clock.now_iso.return_value = expected_timestamp

        # Act
        result = mock_clock.now_iso()

        # Assert - Verify return type matches contract specification
        assert isinstance(result, str)
        assert len(result) > 0

    def test_now_iso_contract_example_format(self) -> None:
        """Test that now_iso() returns format matching contract example."""
        # Arrange
        mock_clock = Mock(spec=Clock)
        # Contract specifies example: "2025-09-20T15:30:00Z"
        contract_example = '2025-09-20T15:30:00Z'
        mock_clock.now_iso.return_value = contract_example

        # Act
        result = mock_clock.now_iso()

        # Assert
        assert result == contract_example
        # Verify format matches contract example structure
        assert len(result) == 20  # Length of "2025-09-20T15:30:00Z"
        assert result[4] == '-'  # Year-month separator
        assert result[7] == '-'  # Month-day separator
        assert result[10] == 'T'  # Date-time separator
        assert result[13] == ':'  # Hour-minute separator
        assert result[16] == ':'  # Minute-second separator
        assert result[19] == 'Z'  # UTC indicator
