"""Tests for domain policies."""

import pytest

from prosemark.domain.models import Binder, BinderItem, NodeId
from prosemark.domain.policies import (
    validate_no_duplicate_ids,
    validate_placeholder_handling,
    validate_tree_structure,
)
from prosemark.exceptions import BinderIntegrityError


class TestValidateNoDuplicateIds:
    """Test validate_no_duplicate_ids policy."""

    def test_validate_no_duplicate_ids_rejects_duplicates(self) -> None:
        """Test policy rejects binders with duplicate NodeId values."""
        # Arrange: Create binder with duplicate NodeId values
        node_id = NodeId('0192f0c1-2345-7123-8abc-def012345678')
        item1 = BinderItem(id_=node_id, display_title='Chapter 1', children=[])
        item2 = BinderItem(id_=node_id, display_title='Chapter 2', children=[])

        # Act & Assert: Validate with policy - should raise BinderIntegrityError
        with pytest.raises(BinderIntegrityError, match='Duplicate NodeId found'):
            validate_no_duplicate_ids([item1, item2])

    def test_validate_no_duplicate_ids_accepts_unique_ids(self) -> None:
        """Test policy accepts binders with unique NodeId values."""
        # Arrange: Create binder with unique NodeId values
        id1 = NodeId('0192f0c1-2345-7123-8abc-def012345678')
        id2 = NodeId('0192f0c1-2345-7456-8abc-def012345678')
        item1 = BinderItem(id_=id1, display_title='Chapter 1', children=[])
        item2 = BinderItem(id_=id2, display_title='Chapter 2', children=[])

        # Act: Validate with policy - should not raise
        validate_no_duplicate_ids([item1, item2])

    def test_validate_no_duplicate_ids_accepts_multiple_none_ids(self) -> None:
        """Test policy allows multiple placeholder items with None id."""
        # Arrange: Create binder with multiple None ids
        item1 = BinderItem(id_=None, display_title='Placeholder 1', children=[])
        item2 = BinderItem(id_=None, display_title='Placeholder 2', children=[])

        # Act: Validate with policy - should not raise
        validate_no_duplicate_ids([item1, item2])

    def test_validate_no_duplicate_ids_detects_nested_duplicates(self) -> None:
        """Test policy detects duplicate NodeIds in nested children."""
        # Arrange: Create binder with duplicate NodeIds in children
        node_id = NodeId('0192f0c1-2345-7123-8abc-def012345678')
        child1 = BinderItem(id_=node_id, display_title='Chapter 1', children=[])
        child2 = BinderItem(id_=node_id, display_title='Chapter 2', children=[])
        parent = BinderItem(id_=None, display_title='Part 1', children=[child1, child2])

        # Act & Assert: Validate with policy - should raise BinderIntegrityError
        with pytest.raises(BinderIntegrityError, match='Duplicate NodeId found'):
            validate_no_duplicate_ids([parent])

    def test_validate_no_duplicate_ids_handles_empty_list(self) -> None:
        """Test policy handles empty item lists gracefully."""
        # Arrange: Empty item list
        items: list[BinderItem] = []

        # Act: Validate with policy - should not raise
        validate_no_duplicate_ids(items)

    def test_validate_no_duplicate_ids_handles_deep_hierarchy(self) -> None:
        """Test policy validates deeply nested hierarchical structures."""
        # Arrange: Create deep hierarchy with unique IDs
        id1 = NodeId('0192f0c1-2345-7123-8abc-def012345678')
        id2 = NodeId('0192f0c1-2345-7456-8abc-def012345678')
        id3 = NodeId('0192f0c1-2345-7789-8abc-def012345678')

        deep_child = BinderItem(id_=id3, display_title='Deep Chapter', children=[])
        middle_child = BinderItem(id_=id2, display_title='Middle Chapter', children=[deep_child])
        parent = BinderItem(id_=id1, display_title='Parent Chapter', children=[middle_child])

        # Act: Validate with policy - should not raise
        validate_no_duplicate_ids([parent])


class TestValidateTreeStructure:
    """Test validate_tree_structure policy."""

    def test_validate_tree_structure_accepts_valid_hierarchy(self) -> None:
        """Test policy accepts properly nested binder structures."""
        # Arrange: Create properly nested binder structure
        id1 = NodeId('0192f0c1-2345-7123-8abc-def012345678')
        id2 = NodeId('0192f0c1-2345-7456-8abc-def012345678')
        child = BinderItem(id_=id1, display_title='Chapter 1', children=[])
        parent = BinderItem(id_=id2, display_title='Part 1', children=[child])

        # Act: Validate tree structure - should not raise
        validate_tree_structure([parent])

    def test_validate_tree_structure_accepts_flat_structure(self) -> None:
        """Test policy accepts flat structures without nesting."""
        # Arrange: Create flat structure
        id1 = NodeId('0192f0c1-2345-7123-8abc-def012345678')
        id2 = NodeId('0192f0c1-2345-7456-8abc-def012345678')
        item1 = BinderItem(id_=id1, display_title='Chapter 1', children=[])
        item2 = BinderItem(id_=id2, display_title='Chapter 2', children=[])

        # Act: Validate tree structure - should not raise
        validate_tree_structure([item1, item2])

    def test_validate_tree_structure_accepts_mixed_hierarchy(self) -> None:
        """Test policy accepts mixed hierarchical and flat structures."""
        # Arrange: Create mixed structure
        id1 = NodeId('0192f0c1-2345-7123-8abc-def012345678')
        id2 = NodeId('0192f0c1-2345-7456-8abc-def012345678')
        id3 = NodeId('0192f0c1-2345-7789-8abc-def012345678')

        # Nested part
        child = BinderItem(id_=id1, display_title='Chapter 1', children=[])
        parent = BinderItem(id_=id2, display_title='Part 1', children=[child])

        # Flat part
        standalone = BinderItem(id_=id3, display_title='Appendix', children=[])

        # Act: Validate tree structure - should not raise
        validate_tree_structure([parent, standalone])

    def test_validate_tree_structure_handles_empty_list(self) -> None:
        """Test policy handles empty item lists gracefully."""
        # Arrange: Empty item list
        items: list[BinderItem] = []

        # Act: Validate tree structure - should not raise
        validate_tree_structure(items)

    def test_validate_tree_structure_handles_placeholders(self) -> None:
        """Test policy handles placeholder items properly."""
        # Arrange: Structure with placeholders
        id1 = NodeId('0192f0c1-2345-7123-8abc-def012345678')
        child = BinderItem(id_=id1, display_title='Chapter 1', children=[])
        placeholder = BinderItem(id_=None, display_title='Future Section', children=[child])

        # Act: Validate tree structure - should not raise
        validate_tree_structure([placeholder])

    def test_validate_tree_structure_rejects_invalid_display_title(self) -> None:
        """Test policy rejects items with non-string display_title."""
        # Arrange: Create item with invalid display_title type
        # We need to bypass the dataclass validation to test this policy
        from unittest.mock import Mock

        invalid_item = Mock()
        invalid_item.display_title = 123  # Invalid: not a string
        invalid_item.children = []

        # Act & Assert: Validate tree structure - should raise BinderIntegrityError
        with pytest.raises(BinderIntegrityError, match='display_title must be a string'):
            validate_tree_structure([invalid_item])

    def test_validate_tree_structure_rejects_invalid_children_type(self) -> None:
        """Test policy rejects items with non-list children."""
        # Arrange: Create item with invalid children type
        # We need to bypass the dataclass validation to test this policy
        from unittest.mock import Mock

        invalid_item = Mock()
        invalid_item.display_title = 'Valid Title'
        invalid_item.children = 'not_a_list'  # Invalid: not a list

        # Act & Assert: Validate tree structure - should raise BinderIntegrityError
        with pytest.raises(BinderIntegrityError, match='children must be a list'):
            validate_tree_structure([invalid_item])


class TestValidatePlaceholderHandling:
    """Test validate_placeholder_handling policy."""

    def test_validate_placeholder_handling_allows_empty_ids(self) -> None:
        """Test policy allows placeholder items with None id."""
        # Arrange: Create binder with placeholder items (id=None)
        placeholder1 = BinderItem(id_=None, display_title='New Section', children=[])
        placeholder2 = BinderItem(id_=None, display_title='Future Chapter', children=[])

        # Act: Validate placeholder handling - should not raise
        validate_placeholder_handling([placeholder1, placeholder2])

    def test_validate_placeholder_handling_allows_mixed_items(self) -> None:
        """Test policy allows mixture of placeholders and regular items."""
        # Arrange: Create binder with mixed item types
        node_id = NodeId('0192f0c1-2345-7123-8abc-def012345678')
        regular_item = BinderItem(id_=node_id, display_title='Chapter 1', children=[])
        placeholder = BinderItem(id_=None, display_title='Future Chapter', children=[])

        # Act: Validate placeholder handling - should not raise
        validate_placeholder_handling([regular_item, placeholder])

    def test_validate_placeholder_handling_allows_nested_placeholders(self) -> None:
        """Test policy allows placeholders in nested structures."""
        # Arrange: Create nested structure with placeholders
        node_id = NodeId('0192f0c1-2345-7123-8abc-def012345678')
        child = BinderItem(id_=node_id, display_title='Chapter 1', children=[])
        placeholder_parent = BinderItem(id_=None, display_title='Part 1', children=[child])

        # Act: Validate placeholder handling - should not raise
        validate_placeholder_handling([placeholder_parent])

    def test_validate_placeholder_handling_handles_empty_list(self) -> None:
        """Test policy handles empty item lists gracefully."""
        # Arrange: Empty item list
        items: list[BinderItem] = []

        # Act: Validate placeholder handling - should not raise
        validate_placeholder_handling(items)

    def test_validate_placeholder_handling_allows_all_placeholders(self) -> None:
        """Test policy allows structures with only placeholders."""
        # Arrange: Create structure with only placeholders
        placeholder1 = BinderItem(id_=None, display_title='Section 1', children=[])
        placeholder2 = BinderItem(id_=None, display_title='Section 2', children=[])
        placeholder_parent = BinderItem(id_=None, display_title='Book', children=[placeholder1, placeholder2])

        # Act: Validate placeholder handling - should not raise
        validate_placeholder_handling([placeholder_parent])

    def test_validate_placeholder_handling_rejects_invalid_placeholder_title(self) -> None:
        """Test policy rejects placeholders with invalid display_title."""
        # Arrange: Create placeholder with invalid display_title
        # We need to bypass the dataclass validation to test this policy
        from unittest.mock import Mock

        invalid_placeholder = Mock()
        invalid_placeholder.id = None  # This is a placeholder
        invalid_placeholder.display_title = ''  # Invalid: empty string
        invalid_placeholder.children = []

        # Act & Assert: Validate placeholder handling - should raise BinderIntegrityError
        with pytest.raises(BinderIntegrityError, match='Placeholder items must have valid display titles'):
            validate_placeholder_handling([invalid_placeholder])


class TestPolicyIntegration:
    """Test policy integration with Binder methods."""

    def test_binder_methods_use_integrity_policies(self) -> None:
        """Test that Binder methods automatically enforce integrity policies."""
        # Arrange: Create binder with policy violations
        node_id = NodeId('0192f0c1-2345-7123-8abc-def012345678')
        item1 = BinderItem(id_=node_id, display_title='Chapter 1', children=[])
        item2 = BinderItem(id_=node_id, display_title='Chapter 2', children=[])

        # Act: Call binder constructor (mutation method) - should raise
        # Assert: Policies automatically enforced via __post_init__
        with pytest.raises(BinderIntegrityError, match='Duplicate NodeId'):
            Binder(roots=[item1, item2])

    def test_binder_validate_integrity_uses_policies(self) -> None:
        """Test that Binder.validate_integrity uses domain policies."""
        # Arrange: Create valid binder first
        id1 = NodeId('0192f0c1-2345-7123-8abc-def012345678')
        id2 = NodeId('0192f0c1-2345-7456-8abc-def012345678')
        item1 = BinderItem(id_=id1, display_title='Chapter 1', children=[])
        item2 = BinderItem(id_=id2, display_title='Chapter 2', children=[])
        binder = Binder(roots=[item1, item2])

        # Act: Call validate_integrity - should not raise
        binder.validate_integrity()


class TestPolicyExceptionHandling:
    """Test policy violation exception handling."""

    def test_policy_violations_raise_specific_exceptions(self) -> None:
        """Test that policy violations raise correct exception types with descriptive messages."""
        # Arrange: Various policy violation scenarios
        node_id = NodeId('0192f0c1-2345-7123-8abc-def012345678')

        # Scenario 1: Duplicate NodeId violation
        duplicate_item1 = BinderItem(id_=node_id, display_title='Chapter 1', children=[])
        duplicate_item2 = BinderItem(id_=node_id, display_title='Chapter 2', children=[])

        # Act: Apply policies to invalid data
        # Assert: Correct exception types with descriptive messages
        with pytest.raises(BinderIntegrityError) as exc_info:
            validate_no_duplicate_ids([duplicate_item1, duplicate_item2])

        assert 'Duplicate NodeId found' in str(exc_info.value)
        assert str(node_id) in str(exc_info.value)

    def test_policy_exception_includes_context(self) -> None:
        """Test that policy exceptions include relevant context information."""
        # Arrange: Policy violation with specific NodeId
        node_id = NodeId('0192f0c1-2345-7123-8abc-def012345678')
        item1 = BinderItem(id_=node_id, display_title='First Item', children=[])
        item2 = BinderItem(id_=node_id, display_title='Second Item', children=[])

        # Act & Assert: Exception should include the problematic NodeId
        with pytest.raises(BinderIntegrityError) as exc_info:
            validate_no_duplicate_ids([item1, item2])

        # Check that the NodeId is included in exception context
        assert len(exc_info.value.args) >= 2  # Message + NodeId context
        assert exc_info.value.args[1] == node_id

    def test_multiple_policy_violations_first_error_wins(self) -> None:
        """Test that when multiple policy violations exist, the first detected error is raised."""
        # Arrange: Binder with duplicate NodeIds (first policy that would fail)
        node_id = NodeId('0192f0c1-2345-7123-8abc-def012345678')
        item1 = BinderItem(id_=node_id, display_title='Chapter 1', children=[])
        item2 = BinderItem(id_=node_id, display_title='Chapter 2', children=[])

        # Act & Assert: Should fail on duplicate IDs policy first
        with pytest.raises(BinderIntegrityError, match='Duplicate NodeId found'):
            validate_no_duplicate_ids([item1, item2])
