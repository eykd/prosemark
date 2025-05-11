"""Pytest configuration file for Prosemark tests."""

import sys
from collections.abc import Generator
from pathlib import Path
from unittest.mock import patch

import pytest

from prosemark.domain.nodes import Node, NodeID

# Add the src directory to the Python path
src_path = Path(__file__).parent.parent / 'src'
sys.path.insert(0, str(src_path))


@pytest.fixture
def node_ids() -> Generator[list[NodeID], None, None]:
    """Fixture to generate unique node IDs."""
    node_ids = [
        '202505111234567890',
        '202505111234567891',
        '202505111234567892',
        '202505111234567893',
        '202505111234567894',
        '202505111234567895',
        '202505111234567896',
        '202505111234567897',
        '202505111234567898',
        '202505111234567899',
        '202505111234567900',
    ]
    with patch.object(Node, 'generate_id', side_effect=node_ids):
        yield node_ids
