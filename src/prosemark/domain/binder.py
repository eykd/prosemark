"""Binder domain model."""

from dataclasses import dataclass, field

from prosemark.domain.models import NodeId


@dataclass
class Item:
    """Represents an item in the binder hierarchy."""

    display_title: str
    id: NodeId | None = None
    children: list['Item'] = field(default_factory=list)  # Improved list initialization
