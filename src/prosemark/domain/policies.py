"""Domain policies for binder integrity validation.

This module provides pure functions that validate binder integrity constraints
to ensure the system maintains consistent and valid binder state throughout
all operations.

All policies follow functional programming principles:
- Pure functions with no side effects
- Take domain objects and return validation results
- Raise appropriate domain exceptions for violations
- Composable and reusable across different use cases
"""

from typing import TYPE_CHECKING

from prosemark.exceptions import BinderIntegrityError

if TYPE_CHECKING:  # pragma: no cover
    from prosemark.domain.models import BinderItem, NodeId


def validate_no_duplicate_ids(items: list['BinderItem']) -> None:
    """Validate that no duplicate NodeId values exist within the binder tree.

    This policy ensures tree integrity by preventing duplicate NodeId references
    that could lead to ambiguous node resolution and data inconsistencies.
    Placeholder items with None id are allowed and ignored.

    Args:
        items: List of root-level BinderItem objects to validate

    Raises:
        BinderIntegrityError: If duplicate NodeId values are found in the tree

    Examples:
        >>> # Valid case - unique NodeIds
        >>> id1 = NodeId('0192f0c1-2345-7123-8abc-def012345678')
        >>> id2 = NodeId('0192f0c1-2345-7456-8abc-def012345678')
        >>> item1 = BinderItem(id=id1, display_title='Chapter 1', children=[])
        >>> item2 = BinderItem(id=id2, display_title='Chapter 2', children=[])
        >>> validate_no_duplicate_ids([item1, item2])  # No exception

        >>> # Invalid case - duplicate NodeIds
        >>> duplicate = BinderItem(id=id1, display_title='Duplicate', children=[])
        >>> validate_no_duplicate_ids([item1, duplicate])  # Raises BinderIntegrityError

    """
    seen_node_ids = set['NodeId']()

    def _collect_node_ids(item: 'BinderItem') -> None:
        """Recursively collect all NodeIds and check for duplicates."""
        if item.id is not None:
            if item.id in seen_node_ids:
                msg = f'Duplicate NodeId found in tree: {item.id}'
                raise BinderIntegrityError(msg, item.id)
            seen_node_ids.add(item.id)

        for child in item.children:
            _collect_node_ids(child)

    for item in items:
        _collect_node_ids(item)


def validate_tree_structure(items: list['BinderItem']) -> None:
    """Validate that all referenced nodes maintain valid hierarchical relationships.

    This policy ensures tree structure integrity by validating that the
    hierarchical structure is well-formed and maintains proper parent-child
    relationships. Currently validates basic structural integrity.

    Args:
        items: List of root-level BinderItem objects to validate

    Raises:
        BinderIntegrityError: If tree structure violations are detected

    Examples:
        >>> # Valid hierarchical structure
        >>> child = BinderItem(id=NodeId('...'), display_title='Chapter 1', children=[])
        >>> parent = BinderItem(id=NodeId('...'), display_title='Part 1', children=[child])
        >>> validate_tree_structure([parent])  # No exception

        >>> # Valid flat structure
        >>> item1 = BinderItem(id=NodeId('...'), display_title='Chapter 1', children=[])
        >>> item2 = BinderItem(id=NodeId('...'), display_title='Chapter 2', children=[])
        >>> validate_tree_structure([item1, item2])  # No exception

    """

    def _validate_item_structure(item: 'BinderItem') -> None:
        """Recursively validate the structure of each item and its children."""
        # Basic structure validation - item should have a display_title
        if not isinstance(item.display_title, str):  # pragma: no cover
            msg = 'BinderItem display_title must be a string'
            raise BinderIntegrityError(msg, item)  # pragma: no cover

        # Validate children list is properly formed
        if not isinstance(item.children, list):  # pragma: no cover
            msg = 'BinderItem children must be a list'
            raise BinderIntegrityError(msg, item)  # pragma: no cover

        # Recursively validate children
        for child in item.children:
            _validate_item_structure(child)

    for item in items:
        _validate_item_structure(item)


def validate_placeholder_handling(items: list['BinderItem']) -> None:
    """Validate that placeholder nodes (without IDs) are properly handled.

    This policy ensures that placeholder items with None id are properly
    supported throughout the tree structure. Placeholders are valid items
    that represent future or organizational nodes without actual content.

    Args:
        items: List of root-level BinderItem objects to validate

    Raises:
        BinderIntegrityError: If placeholder handling violations are detected

    Examples:
        >>> # Valid placeholders
        >>> placeholder1 = BinderItem(id=None, display_title='Future Section', children=[])
        >>> placeholder2 = BinderItem(id=None, display_title='New Chapter', children=[])
        >>> validate_placeholder_handling([placeholder1, placeholder2])  # No exception

        >>> # Valid mixed items
        >>> regular = BinderItem(id=NodeId('...'), display_title='Chapter 1', children=[])
        >>> placeholder = BinderItem(id=None, display_title='Future', children=[])
        >>> validate_placeholder_handling([regular, placeholder])  # No exception

    """

    def _validate_placeholder_item(item: 'BinderItem') -> None:
        """Recursively validate placeholder handling for each item."""
        # Placeholder validation - None id is explicitly allowed
        if item.id is None and (not item.display_title or not isinstance(item.display_title, str)):
            # Placeholders must still have valid display titles
            msg = 'Placeholder items must have valid display titles'
            raise BinderIntegrityError(msg, item)

        # Recursively validate children
        for child in item.children:
            _validate_placeholder_item(child)

    for item in items:
        _validate_placeholder_item(item)
