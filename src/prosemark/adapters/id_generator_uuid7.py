# Copyright (c) 2024 Prosemark Contributors
# This software is licensed under the MIT License

"""UUIDv7-based ID generator implementation."""

from prosemark.domain.models import NodeId
from prosemark.ports.id_generator import IdGenerator


class IdGeneratorUuid7(IdGenerator):
    """Production ID generator using UUIDv7 for temporal ordering.

    This implementation leverages the UUIDv7 format to provide:
    - Globally unique identifiers
    - Temporal ordering capabilities (newer UUIDs sort after older ones)
    - Distributed generation without coordination
    - Compatibility with existing UUID tooling

    The UUIDv7 format embeds a timestamp in the first 48 bits, enabling
    natural chronological sorting while maintaining the randomness properties
    needed for uniqueness across distributed systems.
    """

    def new(self) -> NodeId:
        """Generate a new NodeId using UUIDv7.

        Returns:
            A new NodeId with UUIDv7 format

        """
        return NodeId.generate()
