"""Domain aggregates for Prosemark."""

from dataclasses import dataclass

from .exceptions import BinderIntegrityError
from .value_objects import BinderItem, NodeId


@dataclass(frozen=True)
class Binder:
    """Contains roots list, enforces tree invariants (no duplicates, valid structure)."""

    roots: list[BinderItem]

    def __post_init__(self) -> None:
        """Validate binder invariants after initialization."""
        self._validate_no_duplicates()

    def _validate_no_duplicates(self) -> None:
        """Validate that there are no duplicate NodeIds in the binder."""
        all_ids = self.get_all_ids()
        unique_ids = set(all_ids)

        if len(all_ids) != len(unique_ids):
            # Find which ID is duplicated
            seen = set()
            for node_id in all_ids:
                if node_id in seen:
                    msg = f'Duplicate NodeId found: {node_id}'
                    raise BinderIntegrityError(msg)
                seen.add(node_id)

    def is_empty(self) -> bool:
        """Check if binder has no roots."""
        return len(self.roots) == 0

    def get_all_ids(self) -> list[NodeId]:
        """Get all non-None NodeIds from entire binder hierarchy."""
        all_ids = []
        for root in self.roots:
            all_ids.extend(root.collect_all_ids())
        return all_ids

    def find_by_id(self, node_id: NodeId) -> BinderItem | None:
        """Find item with given NodeId anywhere in binder."""
        for root in self.roots:
            found = root.find_by_id(node_id)
            if found is not None:
                return found
        return None

    def count_placeholders(self) -> int:
        """Count total placeholders in binder."""
        count = 0
        for root in self.roots:
            if root.is_placeholder():
                count += 1
            # Recursively count in children
            count += self._count_placeholders_recursive(root.children)
        return count

    def _count_placeholders_recursive(self, items: list[BinderItem]) -> int:
        """Recursively count placeholders in a list of items."""
        count = 0
        for item in items:
            if item.is_placeholder():
                count += 1
            count += self._count_placeholders_recursive(item.children)
        return count

    def add_root(self, item: BinderItem) -> 'Binder':
        """Add a root item, returning new Binder instance."""
        # Check for duplicate before adding
        if item.id is not None:
            existing_ids = self.get_all_ids()
            if item.id in existing_ids:
                msg = f'Duplicate NodeId: {item.id}'
                raise BinderIntegrityError(msg)

            # Also check for duplicates within the new item itself
            new_item_ids = item.collect_all_ids()
            for new_id in new_item_ids:
                if new_id in existing_ids:
                    msg = f'Duplicate NodeId: {new_id}'
                    raise BinderIntegrityError(msg)

        new_roots = [*list(self.roots), item]
        return Binder(roots=new_roots)

    def remove_by_id(self, node_id: NodeId) -> 'Binder':
        """Remove item with given NodeId, returning new Binder instance."""
        new_roots = []

        for root in self.roots:
            if root.id == node_id:
                # Skip this root (remove it)
                continue
            # Check if we need to remove from children
            new_root = self._remove_from_item(root, node_id)
            if new_root is not None:
                new_roots.append(new_root)

        return Binder(roots=new_roots)

    def _remove_from_item(self, item: BinderItem, node_id: NodeId) -> BinderItem | None:
        """Remove node_id from item's children, return updated item or None if item should be removed."""
        if item.id == node_id:
            return None  # This item should be removed

        new_children = []
        for child in item.children:
            new_child = self._remove_from_item(child, node_id)
            if new_child is not None:
                new_children.append(new_child)

        # Return new item with updated children
        return BinderItem(id=item.id, display_title=item.display_title, children=new_children)

    def insert_root(self, item: BinderItem, position: int) -> 'Binder':
        """Insert root item at specific position, returning new Binder instance."""
        # Check for duplicates
        if item.id is not None:
            existing_ids = self.get_all_ids()
            new_item_ids = item.collect_all_ids()
            for new_id in new_item_ids:
                if new_id in existing_ids:
                    msg = f'Duplicate NodeId: {new_id}'
                    raise BinderIntegrityError(msg)

        new_roots = list(self.roots)
        new_roots.insert(position, item)
        return Binder(roots=new_roots)

    def move_item(self, item_id: NodeId, new_parent_id: NodeId) -> 'Binder':
        """Move item to be child of new parent, returning new Binder instance."""
        # Find the item to move
        item_to_move = self.find_by_id(item_id)
        if item_to_move is None:
            msg = f'Item not found: {item_id}'
            raise ValueError(msg)

        # Find the new parent
        new_parent = self.find_by_id(new_parent_id)
        if new_parent is None:
            msg = f'Parent not found: {new_parent_id}'
            raise ValueError(msg)

        # Remove the item from its current location
        binder_without_item = self.remove_by_id(item_id)

        # Add the item as child of new parent
        return binder_without_item._add_child_to_parent(new_parent_id, item_to_move)

    def _add_child_to_parent(self, parent_id: NodeId, child: BinderItem) -> 'Binder':
        """Add child to parent, returning new Binder instance."""
        new_roots = []

        for root in self.roots:
            new_root = self._add_child_to_item(root, parent_id, child)
            new_roots.append(new_root)

        return Binder(roots=new_roots)

    def _add_child_to_item(self, item: BinderItem, parent_id: NodeId, child: BinderItem) -> BinderItem:
        """Add child to item if it matches parent_id, or recursively to children."""
        if item.id == parent_id:
            # This is the parent, add child
            new_children = [*list(item.children), child]
            return BinderItem(id=item.id, display_title=item.display_title, children=new_children)
        # Recursively check children
        new_children = []
        for child_item in item.children:
            new_children.append(self._add_child_to_item(child_item, parent_id, child))

        return BinderItem(id=item.id, display_title=item.display_title, children=new_children)

    def __repr__(self) -> str:
        """Return string representation."""
        num_roots = len(self.roots)
        if num_roots == 1:
            return 'Binder(1 root)'
        return f'Binder({num_roots} roots)'
