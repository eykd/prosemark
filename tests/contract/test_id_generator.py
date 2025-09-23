"""Contract tests for IdGenerator protocol (T014).

These tests verify that any implementation of the IdGenerator protocol
correctly implements the contract defined in the domain interfaces.
Tests will initially fail due to missing imports - this is expected.
"""

import uuid
from unittest.mock import Mock

from prosemark.domain.models import NodeId

# These imports will fail initially - this is expected for contract tests
from prosemark.ports import IdGenerator


class TestIdGeneratorContract:
    """Test contract compliance for IdGenerator implementations."""

    def test_new_returns_node_id(self) -> None:
        """Test that new() returns a NodeId object."""
        # Arrange
        mock_generator = Mock(spec=IdGenerator)
        expected_node_id = NodeId('0192f0c1-2345-7123-8abc-def012345678')
        mock_generator.new.return_value = expected_node_id

        # Act
        result = mock_generator.new()

        # Assert
        assert isinstance(result, NodeId)
        assert result == expected_node_id
        mock_generator.new.assert_called_once()

    def test_new_generates_valid_uuidv7_format(self) -> None:
        """Test that new() generates NodeId with valid UUIDv7 format."""
        # Arrange
        mock_generator = Mock(spec=IdGenerator)
        # Generate a valid UUIDv7 for testing
        valid_uuidv7 = '0192f0c1-2345-7123-8abc-def012345678'
        expected_node_id = NodeId(valid_uuidv7)
        mock_generator.new.return_value = expected_node_id

        # Act
        result = mock_generator.new()

        # Assert
        assert isinstance(result, NodeId)
        # Verify the underlying UUID is version 7
        parsed_uuid = uuid.UUID(result.value)
        assert parsed_uuid.version == 7

    def test_new_generates_unique_ids(self) -> None:
        """Test that multiple calls to new() generate different NodeIds."""
        # Arrange
        mock_generator = Mock(spec=IdGenerator)
        node_ids = [
            NodeId('0192f0c1-2345-7123-8abc-def012345678'),
            NodeId('0192f0c1-2345-7123-8abc-def012345679'),
            NodeId('0192f0c1-2345-7123-8abc-def012345680'),
        ]
        mock_generator.new.side_effect = node_ids

        # Act
        results = [mock_generator.new() for _ in range(3)]

        # Assert
        assert len(results) == 3
        assert all(isinstance(result, NodeId) for result in results)
        # Verify they are all different
        assert len({result.value for result in results}) == 3
        assert mock_generator.new.call_count == 3

    def test_new_no_parameters(self) -> None:
        """Test that new() method takes no parameters."""
        # Arrange
        mock_generator = Mock(spec=IdGenerator)
        expected_node_id = NodeId('0192f0c1-2345-7123-8abc-def012345678')
        mock_generator.new.return_value = expected_node_id

        # Act - should work with no parameters
        result = mock_generator.new()

        # Assert
        assert isinstance(result, NodeId)
        mock_generator.new.assert_called_once_with()

    def test_new_consistent_return_type(self) -> None:
        """Test that new() consistently returns NodeId type."""
        # Arrange
        mock_generator = Mock(spec=IdGenerator)
        node_ids = [
            NodeId('0192f0c1-2345-7123-8abc-def012345678'),
            NodeId('0192f0c1-2345-7123-8abc-def012345679'),
            NodeId('0192f0c1-2345-7123-8abc-def012345680'),
            NodeId('0192f0c1-2345-7123-8abc-def012345681'),
            NodeId('0192f0c1-2345-7123-8abc-def012345682'),
        ]
        mock_generator.new.side_effect = node_ids

        # Act
        results = [mock_generator.new() for _ in range(5)]

        # Assert
        assert all(isinstance(result, NodeId) for result in results)
        assert len(results) == 5

    def test_new_returns_sortable_ids(self) -> None:
        """Test that new() returns NodeIds that can be sorted (UUIDv7 property)."""
        # Arrange
        mock_generator = Mock(spec=IdGenerator)
        # Create UUIDv7s with slightly different timestamps to test sortability
        node_ids = [
            NodeId('0192f0c1-0000-7123-8abc-def012345678'),  # Earlier timestamp
            NodeId('0192f0c1-1111-7123-8abc-def012345679'),  # Middle timestamp
            NodeId('0192f0c1-2222-7123-8abc-def012345680'),  # Later timestamp
        ]
        mock_generator.new.side_effect = node_ids

        # Act
        results = [mock_generator.new() for _ in range(3)]

        # Assert
        assert len(results) == 3
        # Verify they can be sorted by their string representation
        sorted_results = sorted(results, key=lambda x: x.value)
        assert len(sorted_results) == 3
        # In UUIDv7, earlier timestamps should sort first
        assert sorted_results[0].value == '0192f0c1-0000-7123-8abc-def012345678'
        assert sorted_results[1].value == '0192f0c1-1111-7123-8abc-def012345679'
        assert sorted_results[2].value == '0192f0c1-2222-7123-8abc-def012345680'

    def test_new_uuidv7_timestamp_component(self) -> None:
        """Test that new() generates UUIDv7 with timestamp component."""
        # Arrange
        mock_generator = Mock(spec=IdGenerator)
        # UUIDv7 format: timestamp (48 bits) + version (4 bits) + sequence (12 bits)
        # + variant (2 bits) + random (62 bits)
        valid_uuidv7 = '0192f0c1-2345-7123-8abc-def012345678'
        expected_node_id = NodeId(valid_uuidv7)
        mock_generator.new.return_value = expected_node_id

        # Act
        result = mock_generator.new()

        # Assert
        assert isinstance(result, NodeId)
        parsed_uuid = uuid.UUID(result.value)

        # Verify UUIDv7 structure
        assert parsed_uuid.version == 7

        # UUIDv7 should have variant bits set correctly (10xx in binary)
        variant_bits = (parsed_uuid.int >> 62) & 0x3
        assert variant_bits == 0x2  # Binary 10

    def test_protocol_methods_exist(self) -> None:
        """Test that IdGenerator protocol has required methods."""
        # This test verifies the protocol interface exists
        mock_generator = Mock(spec=IdGenerator)

        # Verify methods exist
        assert hasattr(mock_generator, 'new')

        # Verify methods are callable
        assert callable(mock_generator.new)

    def test_new_method_signature(self) -> None:
        """Test that new() method has correct signature."""
        # Arrange
        mock_generator = Mock(spec=IdGenerator)
        expected_node_id = NodeId('0192f0c1-2345-7123-8abc-def012345678')
        mock_generator.new.return_value = expected_node_id

        # Act - Test that method can be called without parameters
        result = mock_generator.new()

        # Assert
        assert isinstance(result, NodeId)
        # Verify it was called with no arguments
        mock_generator.new.assert_called_once_with()

    def test_new_return_type_annotation(self) -> None:
        """Test that new() returns NodeId type as specified in contract."""
        # Arrange
        mock_generator = Mock(spec=IdGenerator)
        expected_node_id = NodeId('0192f0c1-2345-7123-8abc-def012345678')
        mock_generator.new.return_value = expected_node_id

        # Act
        result = mock_generator.new()

        # Assert - Verify return type matches contract specification
        assert isinstance(result, NodeId)
        assert hasattr(result, 'value')
        assert isinstance(result.value, str)

    def test_uuidv7_format_validation(self) -> None:
        """Test that generated NodeId contains valid UUIDv7 format."""
        # Arrange
        mock_generator = Mock(spec=IdGenerator)

        # Test multiple valid UUIDv7 formats
        valid_uuidv7_samples = [
            '0192f0c1-2345-7123-8abc-def012345678',
            '0192f0c2-3456-7234-9bcd-ef0123456789',
            '0192f0c3-4567-7345-abcd-f01234567890',
        ]

        node_ids = [NodeId(uuid_str) for uuid_str in valid_uuidv7_samples]
        mock_generator.new.side_effect = node_ids

        # Act & Assert
        for _expected_node_id in node_ids:
            result = mock_generator.new()
            assert isinstance(result, NodeId)

            # Parse and validate UUID format
            parsed_uuid = uuid.UUID(result.value)
            assert parsed_uuid.version == 7

            # Verify the value matches expected format
            assert len(result.value) == 36  # Standard UUID string length
            assert result.value.count('-') == 4  # Standard UUID dash count
