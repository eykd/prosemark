"""CLI adapter for the Prosemark application.

This module provides service classes that implement the CLI commands
for the Prosemark application, following the hexagonal architecture pattern.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, NamedTuple

from prosemark.domain.factories import NodeFactory, ProjectFactory
from prosemark.parsers.nodes import NodeParser

if TYPE_CHECKING:  # pragma: no cover
    from collections.abc import Generator, Iterable

    from prosemark.domain.nodes import Node, NodeID
    from prosemark.repositories.project import ProjectRepository


class CLIResult(NamedTuple):
    """Result of a CLI command.

    Attributes:
        success: Whether the command was successful.
        message: A message or messages describing the result.

    """

    success: bool
    message: Iterable[str]


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

    def init_project(self, title: str, description: str | None = None) -> CLIResult:
        """Create a new project.

        Args:
            title: The title of the new project.
            description: Optional description of the project.

        Returns:
            A CLIResult with success status and message about the operation.

        """
        # Create a new project with a root node
        project = ProjectFactory.build(
            root_node=NodeFactory.build(id='_binder', title=title, notecard=description or '')
        )

        # Save the project, which will create the _binder.md file
        self.repository.save_project(project)

        return CLIResult(success=True, message=[f"Project '{title}' initialized successfully."])

    def get_project_info(self) -> CLIResult:
        """Get information about the current project.

        Returns:
            A CLIResult with success status and lines of text with project information.

        """
        project = self.repository.load_project()
        # Try to read the notecard file for the root node
        notecard_content = self.repository.storage.read('_binder notecard')
        if not notecard_content:  # pragma: no cover
            notecard_content = project.root_node.notecard

        lines = [
            f'Project: {project.title}\n',
            f'Description: {notecard_content}\n',
            f'Nodes: {project.get_node_count()}\n',
            '\nMetadata:\n',
        ]

        for key, value in project.root_node.metadata.items():  # pragma: no cover
            lines.append(f'  {key}: {value}\n')

        return CLIResult(success=True, message=lines)

    def add_node(
        self,
        parent_id: str,
        title: str,
        notecard: str = '',
        content: str = '',
        notes: str = '',
        position: int | None = None,
    ) -> CLIResult:
        """Add a new node to the project.

        Args:
            parent_id: The ID of the parent node.
            title: The title of the new node.
            notecard: Brief summary of the node.
            content: Main content of the node.
            notes: Additional notes about the node.
            position: Position to insert the node.

        Returns:
            A CLIResult with success status and message about the operation.

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

        if node is None:  # pragma: no cover
            return CLIResult(success=False, message=[f"Failed to create node: parent '{parent_id}' not found"])

        self.repository.save_project(project)
        self.repository.save_node(node)

        return CLIResult(success=True, message=[f'Node added successfully with ID: {node.id}'])

    def remove_node(self, node_id: NodeID) -> CLIResult:
        """Remove a node from the project.

        Args:
            node_id: The ID of the node to remove.

        Returns:
            A CLIResult with success status and message about the operation.

        """
        project = self.repository.load_project()

        node = project.remove_node(node_id)
        if node:
            self.repository.save_project(project)
            return CLIResult(success=True, message=[f"Node '{node.title}' removed successfully"])
        return CLIResult(success=False, message=[f"Node with ID '{node_id}' not found"])  # pragma: no cover

    def move_node(self, node_id: NodeID, new_parent_id: NodeID, position: int | None = None) -> CLIResult:
        """Move a node to a new parent.

        Args:
            node_id: The ID of the node to move.
            new_parent_id: The ID of the new parent node.
            position: Position to insert the node.

        Returns:
            A CLIResult with success status and message about the operation.

        """
        project = self.repository.load_project()

        success = project.move_node(node_id, new_parent_id, position)
        if success:
            self.repository.save_project(project)
            return CLIResult(success=True, message=['Node moved successfully'])
        return CLIResult(
            success=False, message=[f"Failed to move node '{node_id}' to parent '{new_parent_id}'"]
        )  # pragma: no cover

    def show_node(self, node_id: NodeID) -> CLIResult:
        """Display node content.

        Args:
            node_id: The ID of the node to display.

        Returns:
            A CLIResult with success status and content lines.

        """
        project = self.repository.load_project()

        node = project.get_node_by_id(node_id)
        if not node:  # pragma: no cover
            return CLIResult(success=False, message=[f"Node with ID '{node_id}' not found"])

        self.repository.load_node_content(node)

        lines = [f'Title: {node.title}\n\n']
        if node.notecard:  # pragma: no branch
            lines.extend((
                'Notecard:\n',
                node.notecard.rstrip(),
                '\n\n',
            ))

        if node.content:  # pragma: no branch
            lines.extend((
                'Content:\n',
                node.content.rstrip(),
                '\n\n',
            ))

        if node.notes:  # pragma: no branch
            lines.extend((
                'Notes:\n',
                node.notes.rstrip(),
                '\n',
            ))

        return CLIResult(success=True, message=lines)

    def edit_node(self, node_id: NodeID, edited_content: str | None) -> CLIResult:
        """Edit node content.

        Args:
            node_id: The ID of the node to edit.
            edited_content: The edited content from the editor, or None if aborted.

        Returns:
            A CLIResult with success status and message about the operation.

        """
        project = self.repository.load_project()

        node = project.get_node_by_id(node_id)
        if not node:  # pragma: no cover
            return CLIResult(success=False, message=[f"Node with ID '{node_id}' not found"])

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
            return CLIResult(success=True, message=['Node updated successfully'])

        return CLIResult(success=False, message=['Edit aborted'])  # pragma: no cover

    def prepare_node_for_editor(self, node_id: NodeID) -> CLIResult:
        """Prepare node content for editing.

        Args:
            node_id: The ID of the node to edit.

        Returns:
            A CLIResult with success status and formatted content.

        """
        project = self.repository.load_project()

        node = project.get_node_by_id(node_id)
        if not node:  # pragma: no cover
            return CLIResult(success=False, message=[f"Node with ID '{node_id}' not found"])

        self.repository.load_node_content(node)

        # Format the content for the editor
        editor_content = NodeParser.prepare_for_editor(node)
        return CLIResult(success=True, message=[editor_content])

    def get_project_structure(self, node_id: NodeID | None = None) -> CLIResult:
        """Get the project structure.

        Args:
            node_id: Optional ID of the node to start from (defaults to root).

        Returns:
            A CLIResult with success status and generator of structure lines.

        """
        project = self.repository.load_project()

        if node_id:  # pragma: no cover
            start_node = project.get_node_by_id(node_id)
            if not start_node:
                return CLIResult(success=False, message=[f"Node with ID '{node_id}' not found"])
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

        return CLIResult(success=True, message=get_node_lines(start_node))
