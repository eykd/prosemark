# Copyright (c) 2024 Prosemark Contributors
# This software is licensed under the MIT License

"""Simple ID generator implementation."""

from prosemark.domain.models import NodeId
from prosemark.ports.id_generator import IdGenerator


class SimpleIdGenerator(IdGenerator):
    """Basic UUIDv7-based ID generator for production use."""

    def new(self) -> NodeId:
        """Generate a new unique NodeId using UUIDv7.

        Returns:
            A new unique NodeId instance using UUIDv7 format

        """
        return NodeId.generate()
