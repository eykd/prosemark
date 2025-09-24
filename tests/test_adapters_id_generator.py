"""Tests for the SimpleIdGenerator adapter."""

from prosemark.adapters.id_generator import SimpleIdGenerator
from prosemark.domain.models import NodeId
from prosemark.ports.id_generator import IdGenerator


class TestSimpleIdGenerator:
    """Test the SimpleIdGenerator implementation."""

    def test_implements_id_generator_interface(self) -> None:
        """Test that SimpleIdGenerator implements the IdGenerator interface."""
        generator = SimpleIdGenerator()
        assert isinstance(generator, IdGenerator)

    def test_new_generates_valid_node_id(self) -> None:
        """Test that new() generates a valid NodeId."""
        generator = SimpleIdGenerator()
        node_id = generator.new()

        assert isinstance(node_id, NodeId)
        assert len(str(node_id)) == 36  # Standard UUID format
        assert str(node_id).count('-') == 4  # UUID has 4 hyphens

    def test_new_generates_unique_ids(self) -> None:
        """Test that new() generates unique IDs on successive calls."""
        generator = SimpleIdGenerator()

        # Generate multiple IDs
        ids = [generator.new() for _ in range(10)]

        # All should be NodeId instances
        assert all(isinstance(node_id, NodeId) for node_id in ids)

        # All should be unique
        assert len({str(node_id) for node_id in ids}) == 10

    def test_new_uses_uuidv7_format(self) -> None:
        """Test that new() generates UUIDv7 format IDs."""
        generator = SimpleIdGenerator()
        node_id = generator.new()

        # UUIDv7 has version 7 in the 4th hex digit of the 3rd group
        uuid_str = str(node_id)
        version_digit = uuid_str[14]  # Position of version digit in UUID string
        assert version_digit == '7', f'Expected UUIDv7 but got version {version_digit}'
