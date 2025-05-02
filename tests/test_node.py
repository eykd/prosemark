from __future__ import annotations

import uuid
from typing import Any

import pytest

from prosemark.domain.node import Node


def test_node_initialization() -> None:
    """Test that a Node can be initialized with default and custom values."""
    # Test with default values
    node1 = Node()
    assert isinstance(node1.id, str)
    assert node1.title == ""
    assert node1.notecard == ""
    assert node1.content == ""
    assert node1.notes == ""
    assert node1.metadata == {}
    assert node1.parent is None
    assert node1.children == []

    # Test with custom values
    custom_id = str(uuid.uuid4())
    metadata = {"key1": "value1", "key2": 42}
    parent_node = Node()
    child_node = Node()
    
    node2 = Node(
        id=custom_id,
        title="Test Title",
        notecard="Test Notecard",
        content="Test Content",
        notes="Test Notes",
        metadata=metadata,
        parent=parent_node,
        children=[child_node],
    )
    
    assert node2.id == custom_id
    assert node2.title == "Test Title"
    assert node2.notecard == "Test Notecard"
    assert node2.content == "Test Content"
    assert node2.notes == "Test Notes"
    assert node2.metadata == metadata
    assert node2.parent is parent_node
    assert node2.children == [child_node]
    assert child_node.parent is node2  # Child's parent should be set
