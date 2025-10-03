"""Contract tests for Binder.roots iteration and materialized node filtering.

These tests verify that Binder.roots provides access to root-level items and that
filtering for materialized nodes (node_id is not None) works correctly.
"""

from prosemark.domain.models import Binder, BinderItem, NodeId


def test_binder_roots_returns_list() -> None:
    """Binder.roots returns list of BinderItems."""
    binder = Binder(roots=[])
    assert isinstance(binder.roots, list)


def test_empty_binder_filter_returns_empty() -> None:
    """Filtering empty binder returns empty list."""
    binder = Binder(roots=[])
    result = [item.node_id for item in binder.roots if item.node_id is not None]
    assert result == []


def test_all_placeholders_filter_returns_empty() -> None:
    """Filtering all-placeholder binder returns empty list."""
    binder = Binder(
        roots=[
            BinderItem(display_title='P1', node_id=None),
            BinderItem(display_title='P2', node_id=None),
        ]
    )
    result = [item.node_id for item in binder.roots if item.node_id is not None]
    assert result == []


def test_filter_preserves_order() -> None:
    """Filtering maintains binder order for materialized nodes."""
    id1, id2 = NodeId.generate(), NodeId.generate()
    binder = Binder(
        roots=[
            BinderItem(display_title='P', node_id=None),
            BinderItem(display_title='M1', node_id=id1),
            BinderItem(display_title='P2', node_id=None),
            BinderItem(display_title='M2', node_id=id2),
        ]
    )
    result = [item.node_id for item in binder.roots if item.node_id is not None]
    assert result == [id1, id2]


def test_all_materialized_returns_all() -> None:
    """Filtering all-materialized binder returns all node IDs."""
    ids = [NodeId.generate() for _ in range(3)]
    binder = Binder(roots=[BinderItem(display_title=f'Ch{i}', node_id=node_id) for i, node_id in enumerate(ids)])
    result = [item.node_id for item in binder.roots if item.node_id is not None]
    assert result == ids


def test_single_materialized_root() -> None:
    """Filtering single materialized root returns single node ID."""
    node_id = NodeId.generate()
    binder = Binder(roots=[BinderItem(display_title='Chapter', node_id=node_id)])
    result = [item.node_id for item in binder.roots if item.node_id is not None]
    assert result == [node_id]


def test_binder_item_is_materialized_property() -> None:
    """BinderItem.is_materialized() correctly identifies materialized items."""
    placeholder = BinderItem(display_title='Placeholder', node_id=None)
    materialized = BinderItem(display_title='Real', node_id=NodeId.generate())

    assert not placeholder.is_materialized()
    assert materialized.is_materialized()


def test_binder_item_is_root_property() -> None:
    """BinderItem.is_root() correctly identifies root items."""
    root = BinderItem(display_title='Root', node_id=None)
    child = BinderItem(display_title='Child', node_id=None, parent=root)

    assert root.is_root()
    assert not child.is_root()
