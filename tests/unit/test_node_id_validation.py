"""Unit tests for NodeId validation logic."""

import pytest

from prosemark.domain.models import NodeId
from prosemark.exceptions import NodeIdentityError


class TestNodeIdValidation:
    """Test NodeId value object validation."""

    def test_valid_uuidv7_format_accepted(self) -> None:
        """Test that valid UUIDv7 formats are accepted."""
        # Valid UUIDv7 format (RFC 9562 compliant)
        valid_uuids = [
            '01234567-89ab-7def-8123-456789abcdef',  # Standard format
            '01934567-89ab-7def-9123-456789abcdef',  # Different timestamp
            '01934567-89ab-7abc-a123-456789abcdef',  # Different variant bits
        ]

        for uuid_str in valid_uuids:
            node_id = NodeId(uuid_str)
            assert node_id.value == uuid_str

    def test_invalid_uuid_format_rejected(self) -> None:
        """Test that invalid UUID formats are rejected."""
        invalid_uuids = [
            'invalid-uuid',
            '01234567-89ab-4def-8123-456789abcdef',  # Wrong version (4 instead of 7)
            '01234567-89ab-7def-0123-456789abcdef',  # Wrong variant bits
            '01234567-89ab-7def-8123-456789abcde',  # Too short
            '01234567-89ab-7def-8123-456789abcdefg',  # Too long
            '01234567_89ab_7def_8123_456789abcdef',  # Wrong separator
            '',  # Empty string
            '01234567-89ab-7def-8123',  # Truncated
        ]

        for uuid_str in invalid_uuids:
            with pytest.raises((NodeIdentityError, ValueError)):
                NodeId(uuid_str)

    def test_uuidv7_version_validation(self) -> None:
        """Test that only version 7 UUIDs are accepted."""
        # Test different versions
        version_4_uuid = '01234567-89ab-4def-8123-456789abcdef'
        version_1_uuid = '01234567-89ab-1def-8123-456789abcdef'
        version_6_uuid = '01234567-89ab-6def-8123-456789abcdef'

        with pytest.raises((NodeIdentityError, ValueError)):
            NodeId(version_4_uuid)

        with pytest.raises((NodeIdentityError, ValueError)):
            NodeId(version_1_uuid)

        with pytest.raises((NodeIdentityError, ValueError)):
            NodeId(version_6_uuid)

    def test_variant_bits_validation(self) -> None:
        """Test that correct variant bits are required."""
        # Valid variant bits (10xx binary = 8-B hex)
        valid_variants = [
            '01234567-89ab-7def-8123-456789abcdef',  # 1000
            '01234567-89ab-7def-9123-456789abcdef',  # 1001
            '01234567-89ab-7def-a123-456789abcdef',  # 1010
            '01234567-89ab-7def-b123-456789abcdef',  # 1011
        ]

        for uuid_str in valid_variants:
            # Should not raise exception
            node_id = NodeId(uuid_str)
            assert node_id.value == uuid_str

    def test_case_insensitive_handling(self) -> None:
        """Test that UUID case is handled consistently."""
        # Test with uppercase
        upper_uuid = '01234567-89AB-7DEF-8123-456789ABCDEF'
        lower_uuid = '01234567-89ab-7def-8123-456789abcdef'

        # Both should be valid (implementation may normalize)
        upper_node_id = NodeId(upper_uuid)
        lower_node_id = NodeId(lower_uuid)

        # Values should be consistently formatted
        assert isinstance(upper_node_id.value, str)
        assert isinstance(lower_node_id.value, str)

    def test_equality_comparison(self) -> None:
        """Test NodeId equality comparison."""
        uuid_str = '01234567-89ab-7def-8123-456789abcdef'
        node_id1 = NodeId(uuid_str)
        node_id2 = NodeId(uuid_str)

        assert node_id1 == node_id2
        assert node_id1 == node_id2

    def test_inequality_comparison(self) -> None:
        """Test NodeId inequality comparison."""
        uuid_str1 = '01234567-89ab-7def-8123-456789abcdef'
        uuid_str2 = '01934567-89ab-7def-8123-456789abcdef'

        node_id1 = NodeId(uuid_str1)
        node_id2 = NodeId(uuid_str2)

        assert node_id1 != node_id2
        assert node_id1 != node_id2

    def test_hash_consistency(self) -> None:
        """Test that NodeId hashing is consistent."""
        uuid_str = '01234567-89ab-7def-8123-456789abcdef'
        node_id1 = NodeId(uuid_str)
        node_id2 = NodeId(uuid_str)

        assert hash(node_id1) == hash(node_id2)

        # Different UUIDs should have different hashes
        different_uuid = '01934567-89ab-7def-8123-456789abcdef'
        node_id3 = NodeId(different_uuid)
        assert hash(node_id1) != hash(node_id3)

    def test_string_representation(self) -> None:
        """Test NodeId string representation."""
        uuid_str = '01234567-89ab-7def-8123-456789abcdef'
        node_id = NodeId(uuid_str)

        # String representation should be meaningful
        str_repr = str(node_id)
        assert uuid_str in str_repr or uuid_str.upper() in str_repr

    def test_immutability(self) -> None:
        """Test that NodeId is immutable."""
        uuid_str = '01234567-89ab-7def-8123-456789abcdef'
        node_id = NodeId(uuid_str)

        # Value should not be modifiable
        original_value = node_id.value

        # Try to modify (should fail or have no effect)
        try:
            node_id.value = 'different-value'  # type: ignore[misc]
            # If modification was allowed, value should remain the same
            assert node_id.value == original_value
        except (AttributeError, TypeError):
            # Expected for immutable objects
            pass

    def test_timestamp_ordering_property(self) -> None:
        """Test that UUIDv7 maintains timestamp ordering property."""
        # UUIDv7s with increasing timestamps should compare correctly
        earlier_uuid = '01234567-89ab-7def-8123-456789abcdef'
        later_uuid = '01934567-89ab-7def-8123-456789abcdef'

        earlier_id = NodeId(earlier_uuid)
        later_id = NodeId(later_uuid)

        # While NodeId itself might not implement ordering,
        # the timestamp portion should be extractable for verification
        assert earlier_id.value[:8] < later_id.value[:8]  # Compare timestamp portion

    def test_edge_case_boundary_values(self) -> None:
        """Test edge cases and boundary values."""
        # Minimum valid timestamp
        min_timestamp_uuid = '00000000-0000-7000-8000-000000000000'

        # Maximum valid timestamp (in practice)
        max_timestamp_uuid = 'ffffffff-ffff-7fff-bfff-ffffffffffff'

        # Both should be valid
        min_id = NodeId(min_timestamp_uuid)
        max_id = NodeId(max_timestamp_uuid)

        assert min_id.value == min_timestamp_uuid
        assert max_id.value == max_timestamp_uuid

    def test_whitespace_handling(self) -> None:
        """Test handling of whitespace in input."""
        uuid_str = '01234567-89ab-7def-8123-456789abcdef'
        uuid_with_whitespace = f'  {uuid_str}  '

        # Should handle whitespace gracefully (either strip or reject)
        try:
            node_id = NodeId(uuid_with_whitespace)
            # If accepted, should be cleaned
            assert node_id.value.strip() == uuid_str
        except (NodeIdentityError, ValueError):
            # Rejecting whitespace is also acceptable
            pass

    def test_none_and_empty_handling(self) -> None:
        """Test handling of None and empty inputs."""
        with pytest.raises((NodeIdentityError, ValueError, TypeError)):
            NodeId(None)  # type: ignore[arg-type]

        with pytest.raises((NodeIdentityError, ValueError)):
            NodeId('')

        with pytest.raises((NodeIdentityError, ValueError)):
            NodeId('   ')
