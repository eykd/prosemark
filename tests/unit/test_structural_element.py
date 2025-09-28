"""Unit tests for StructuralElement value object.

Tests the StructuralElement value object for representing valid
markdown list items with optional links.
"""

import pytest

from prosemark.domain.models import NodeId
from prosemark.domain.structural_element import StructuralElement


class TestStructuralElement:
    """Unit tests for StructuralElement value object."""

    def test_structural_element_creation(self) -> None:
        """Test creating a StructuralElement instance with valid data."""
        node_id = NodeId.generate()
        element = StructuralElement(indent_level=2, title='Test Item', node_id=node_id, line_number=5)

        assert element.indent_level == 2
        assert element.title == 'Test Item'
        assert element.node_id == node_id
        assert element.line_number == 5

    def test_structural_element_without_node_id(self) -> None:
        """Test creating a StructuralElement without a node_id (placeholder)."""
        element = StructuralElement(indent_level=1, title='Placeholder Item', node_id=None, line_number=3)

        assert element.indent_level == 1
        assert element.title == 'Placeholder Item'
        assert element.node_id is None
        assert element.line_number == 3

    def test_structural_element_validation_rules(self) -> None:
        """Test validation rules for StructuralElement fields."""
        # Test negative indent level validation
        with pytest.raises(ValueError, match='indent_level must be non-negative'):
            StructuralElement(indent_level=-1, title='Test', node_id=None, line_number=1)

        # Test empty title validation
        with pytest.raises(ValueError, match='title must not be empty'):
            StructuralElement(indent_level=0, title='', node_id=None, line_number=1)

        # Test whitespace-only title validation
        with pytest.raises(ValueError, match='title must not be empty'):
            StructuralElement(indent_level=0, title='   ', node_id=None, line_number=1)

        # Test non-positive line number validation
        with pytest.raises(ValueError, match='line_number must be positive'):
            StructuralElement(indent_level=0, title='Test', node_id=None, line_number=0)

        with pytest.raises(ValueError, match='line_number must be positive'):
            StructuralElement(indent_level=0, title='Test', node_id=None, line_number=-1)

    def test_structural_element_equality(self) -> None:
        """Test equality comparison between StructuralElement instances."""
        node_id = NodeId.generate()

        element1 = StructuralElement(indent_level=2, title='Test Item', node_id=node_id, line_number=5)

        element2 = StructuralElement(indent_level=2, title='Test Item', node_id=node_id, line_number=5)

        element3 = StructuralElement(indent_level=3, title='Different Item', node_id=None, line_number=10)

        # Test equality
        assert element1 == element2
        assert element1 != element3
        assert element2 != element3

        # Test that elements with same data but different objects are equal
        assert element1 is not element2
        assert element1 == element2
