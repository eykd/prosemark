"""Project repository implementation.

This module provides the ProjectRepository class which is responsible for loading
and saving Projects and Nodes from/to storage, acting as an adapter between the
domain models and the storage system.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import yaml

from prosemark.domain.nodes import Node
from prosemark.domain.projects import Project
from prosemark.parsers.nodes import NodeParser
from prosemark.parsers.outlines import OutlineNode, OutlineNodeType, OutlineParser

if TYPE_CHECKING:  # pragma: no cover
    from prosemark.storages.base import NodeStoragePort


class ProjectRepository:
    """Repository for loading and saving Projects and Nodes.

    This class acts as an adapter between the domain models (Project and Node)
    and the storage system, following the hexagonal architecture pattern.

    Attributes:
        storage: The storage adapter used to read and write nodes.

    """

    def __init__(self, storage: NodeStoragePort) -> None:
        """Initialize the repository with a storage adapter.

        Args:
            storage: The storage adapter used to read and write nodes.

        """
        self.storage = storage

    def load_project(self) -> Project:
        """Load a project from storage.

        Returns:
            The loaded Project object.

        """
        # First stage: Load the binder node
        binder_content = self.storage.get_binder()
        if not binder_content:
            # Handle case of new/empty project
            return Project(name='New Project')

        # Second stage: Parse the outline structure
        outline_root = OutlineParser.parse(binder_content)

        # Create project and build node structure
        project = Project(name='Project')  # Default name
        self.build_node_structure(project, outline_root)

        return project

    def save_project(self, project: Project) -> None:
        """Save a project to storage.

        Args:
            project: The Project object to save.

        """
        # Update the binder to reflect the current structure
        binder_content = self.generate_binder_content(project)
        self.storage.write('_binder', binder_content)

        # Save any modified nodes to storage
        # In a real implementation, we would track modified nodes
        # and only save those that have changed
        self.save_node_recursive(project.root_node)

    def load_node_content(self, node: Node) -> None:
        """Load the full content of a node from storage.

        Args:
            node: The Node object to load content for.

        """
        node_content = self.storage.read(node.id)
        if node_content:
            self.parse_node_content(node, node_content)

    def save_node(self, node: Node) -> None:
        """Save a node to storage.

        Args:
            node: The Node object to save.

        """
        node_content = self.serialize_node_content(node)
        self.storage.write(node.id, node_content)

    def build_node_structure(self, project: Project, outline_root: OutlineNode) -> None:
        """Build the node structure from the parsed outline.

        Args:
            project: The Project object to build the structure for.
            outline_root: The root OutlineNode from the parsed outline.

        """
        # Process document children
        for child in outline_root.children:
            if child.type == OutlineNodeType.LIST:
                # Process the list items
                self.process_list_items(project.root_node, child)
            # Ignore TEXT nodes in the binder

    def process_list_items(self, parent_node: Node, list_node: OutlineNode) -> None:
        """Process list items from the outline and create corresponding nodes.

        Args:
            parent_node: The parent Node to add children to.
            list_node: The OutlineNode containing list items.

        """
        for item in list_node.children:
            if item.type == OutlineNodeType.LIST_ITEM:  # pragma: no branch
                # Extract node ID and title from the list item content
                node_info = self.parse_list_item(item.content)

                # Create a new node
                node = Node(
                    node_id=node_info.get('id'),
                    title=node_info.get('title', ''),
                )

                # Add to parent
                parent_node.add_child(node)

                # Process nested lists if any
                for child in item.children:
                    if child.type == OutlineNodeType.LIST:  # pragma: no branch
                        self.process_list_items(node, child)

    def parse_list_item(self, content: str) -> dict[str, str]:
        """Parse a list item content to extract node information.

        Args:
            content: The content of the list item.

        Returns:
            A dictionary containing the node ID and title.

        """
        # Simple parsing: assume format is "- ID: Title"
        content_stripped = content.strip()

        # Remove list marker if present
        if content_stripped.startswith(('- ', '* ', '+ ')):  # pragma: no branch
            content_stripped = content_stripped[2:].strip()

        parts = content_stripped.split(':', 1)
        if len(parts) == 2:
            # Extract ID and title
            return {'id': parts[0].strip(), 'title': parts[1].strip()}

        # Fallback: use the whole content as title (without list marker)
        return {'title': content_stripped}

    def generate_binder_content(self, project: Project) -> str:
        """Generate the binder content from the project structure.

        Args:
            project: The Project object to generate the binder for.

        Returns:
            The binder content as a string.

        """
        lines = [f'# {project.name}\n\n']

        # Add project description if available
        if project.description:
            lines.append(f'{project.description}\n\n')

        # Generate the structure as a nested list - skip the root node itself
        for child in project.root_node.children:
            self.append_node_to_binder(child, lines, 0)

        return ''.join(lines)

    def append_node_to_binder(self, node: Node, lines: list[str], level: int) -> None:
        """Append a node and its children to the binder content.

        Args:
            node: The Node to append.
            lines: The list of lines to append to.
            level: The indentation level.

        """
        indent = '  ' * level
        lines.append(f'{indent}- {node.id}: {node.title}\n')

        for child in node.children:
            self.append_node_to_binder(child, lines, level + 1)

    def save_node_recursive(self, node: Node) -> None:
        """Save a node and all its children recursively.

        Args:
            node: The Node to save.

        """
        self.save_node(node)

        for child in node.children:
            self.save_node_recursive(child)

    def serialize_node_content(self, node: Node) -> str:
        """Serialize a node's content to a string.

        Args:
            node: The Node to serialize.

        Returns:
            The serialized node content.

        """
        # Create a dictionary with all node data
        node_data = {
            'id': node.id,
            'title': node.title,
            'notecard': node.notecard,
            'content': node.content,
            'notes': node.notes,
            'metadata': node.metadata,
        }

        # Use NodeParser to serialize
        return NodeParser.serialize(node_data)

    def parse_node_content(self, node: Node, content: str) -> None:
        """Parse node content and update the node object.

        Args:
            node: The Node to update.
            content: The serialized node content.

        """
        try:
            # Use NodeParser to parse the content
            node_data = NodeParser.parse(content, node.id)

            # Update node properties
            node.title = node_data.get('title', node.title)
            node.notecard = node_data.get('notecard', node.notecard)
            node.content = node_data.get('content', node.content)
            node.notes = node_data.get('notes', node.notes)

            # Update metadata
            metadata = node_data.get('metadata')
            if metadata and isinstance(metadata, dict):
                node.metadata.update(metadata)

        except (ValueError, yaml.YAMLError):
            # If parsing fails, treat as raw content but preserve original properties
            node.content = content
            # Note: We don't modify title, notecard, notes, or metadata when parsing fails
