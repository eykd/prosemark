"""CLI adapter for the Prosemark application.

This module provides service classes that implement the CLI commands
for the Prosemark application, following the hexagonal architecture pattern.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from prosemark.domain.factories import NodeFactory, ProjectFactory
from prosemark.parsers.nodes import NodeParser

if TYPE_CHECKING:  # pragma: no cover
    from collections.abc import Generator

    from prosemark.domain.nodes import Node, NodeID
    from prosemark.repositories.project import ProjectRepository


class CliService:
    """Service class implementing CLI commands for the Prosemark application.

    This class provides methods that implement the business logic for each CLI command,
    separating the command interface from the implementation details.

    Attributes:
        repository: The project repository used to load and save projects and nodes.
    """

    def __init__(self, repository: ProjectRepository) -> None:
        """Initialize the CLI service.

        Args:
            repository: The project repository to use.
        """
        self.repository = repository

    def init_project(self, title: str, description: str | None = None) -> str:
        """Create a new project.

        Args:
            title: The title of the new project.
            description: Optional description of the project.

        Returns:
            A message indicating success.
        """
        # Create a new project with a root node
        project = ProjectFactory.build(
            root_node=NodeFactory.build(id='_binder', title=title, notecard=description or '')
        )

        # Save the project, which will create the _binder.md file
        self.repository.save_project(project)

        return f"Project '{title}' initialized successfully"

    def get_project_info(self) -> Generator[str, None, None]:
        """Get information about the current project.

        Yields:
            Lines of text with project information.
        """
        project = self.repository.load_project()
        # Try to read the notecard file for the root node
        notecard_content = self.repository.storage.read('_binder notecard')
        if not notecard_content:
            notecard_content = project.root_node.notecard

        yield f'Project: {project.title}\n'
        yield f'Description: {notecard_content}\n'
        yield f'Nodes: {project.get_node_count()}\n'

        yield '\nMetadata:\n'
        for key, value in project.root_node.metadata.items():
            yield f'  {key}: {value}\n'

    def add_node(
        self,
        parent_id: str,
        title: str,
        notecard: str = '',
        content: str = '',
        notes: str = '',
        position: int | None = None,
    ) -> str:
        """Add a new node to the project.

        Args:
            parent_id: The ID of the parent node.
            title: The title of the new node.
            notecard: Brief summary of the node.
            content: Main content of the node.
            notes: Additional notes about the node.
            position: Position to insert the node.

        Returns:
            A message with the ID of the newly created node.
        """
        project = self.repository.load_project()

        node = project.create_node(
            parent_id=parent_id,
            title=title,
            notecard=notecard,
            content=content,
            notes=notes,
            position=position,
        )
        self.repository.save_project(project)
        self.repository.save_node(node)

        return f'Node added successfully with ID: {node.id}'

    def remove_node(self, node_id: NodeID) -> str:
        """Remove a node from the project.

        Args:
            node_id: The ID of the node to remove.

        Returns:
            A message indicating success or failure.
        """
        project = self.repository.load_project()

        node = project.remove_node(node_id)
        if node:
            self.repository.save_project(project)
            return f"Node '{node.title}' removed successfully"
        else:
            return f"Node with ID '{node_id}' not found"

    def move_node(self, node_id: NodeID, new_parent_id: NodeID, position: int | None = None) -> str:
        """Move a node to a new parent.

        Args:
            node_id: The ID of the node to move.
            new_parent_id: The ID of the new parent node.
            position: Position to insert the node.

        Returns:
            A message indicating success or failure.
        """
        project = self.repository.load_project()

        success = project.move_node(node_id, new_parent_id, position)
        if success:
            self.repository.save_project(project)
            return 'Node moved successfully'
        else:
            return f"Failed to move node '{node_id}' to parent '{new_parent_id}'"

    def show_node(self, node_id: NodeID) -> tuple[bool, list[str]]:
        """Display node content.

        Args:
            node_id: The ID of the node to display.

        Returns:
            A tuple containing a success flag and a list of content lines.
        """
        project = self.repository.load_project()

        node = project.get_node_by_id(node_id)
        if not node:
            return False, [f"Node with ID '{node_id}' not found"]

        self.repository.load_node_content(node)

        lines = [f'Title: {node.title}']
        if node.notecard:
            lines.append(f'\nNotecard: {node.notecard}')

        if node.content:
            lines.extend((
                '\nContent:',
                node.content,
            ))

        if node.notes:
            lines.extend((
                '\nNotes:',
                node.notes,
            ))

        return True, lines

    def edit_node(self, node_id: NodeID, edited_content: str | None) -> tuple[bool, str]:
        """Edit node content.

        Args:
            node_id: The ID of the node to edit.
            edited_content: The edited content from the editor, or None if aborted.

        Returns:
            A tuple containing a success flag and a message.
        """
        project = self.repository.load_project()

        node = project.get_node_by_id(node_id)
        if not node:
            return False, f"Node with ID '{node_id}' not found"

        self.repository.load_node_content(node)

        # If the user saved changes (didn't abort)
        if edited_content is not None:
            # Parse the edited content back into a Node
            updated_node = NodeParser.parse_from_editor(node_id, edited_content)

            # Update the node with the edited values
            node.title = updated_node.title
            node.notecard = updated_node.notecard
            node.notes = updated_node.notes
            node.content = updated_node.content
            node.metadata.update(updated_node.metadata)

            # Save the updated node
            self.repository.save_node(node)
            return True, 'Node updated successfully'
        
        return False, 'Edit aborted'

    def prepare_node_for_editor(self, node_id: NodeID) -> tuple[bool, str]:
        """Prepare node content for editing.

        Args:
            node_id: The ID of the node to edit.

        Returns:
            A tuple containing a success flag and the formatted content.
        """
        project = self.repository.load_project()

        node = project.get_node_by_id(node_id)
        if not node:
            return False, f"Node with ID '{node_id}' not found"

        self.repository.load_node_content(node)

        # Format the content for the editor
        editor_content = NodeParser.prepare_for_editor(node)
        return True, editor_content

    def get_project_structure(self, node_id: NodeID | None = None) -> tuple[bool, Generator[str, None, None]]:
        """Get the project structure.

        Args:
            node_id: Optional ID of the node to start from (defaults to root).

        Returns:
            A tuple containing a success flag and a generator of structure lines.
        """
        project = self.repository.load_project()

        if node_id:
            start_node = project.get_node_by_id(node_id)
            if not start_node:
                return False, (line for line in [f"Node with ID '{node_id}' not found"])
        else:
            start_node = project.root_node

        def get_node_lines(node: Node, level: int = 0) -> Generator[str, None, None]:
            if level == 0:
                yield f'{node.id} - {node.title}\n'
            else:
                indent = '  ' * (level - 1)
                yield f'{indent}- {node.id} {node.title}\n'
            for child in node.children:
                yield from get_node_lines(child, level + 1)

        return True, get_node_lines(start_node)
