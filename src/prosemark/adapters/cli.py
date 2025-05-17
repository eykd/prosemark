"""CLI adapter for the Prosemark application.

This module provides service classes that implement the CLI commands
for the Prosemark application, following the hexagonal architecture pattern.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, NamedTuple

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
        data: Optional data returned by the command.

    """

    success: bool
    message: Iterable[str] | str
    data: Any = None


class CLIService:
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

    def init_project(self, title: str, card: str | None = None) -> CLIResult:
        """Create a new project.

        Args:
            title: The title of the new project.
            card: Optional brief summary of the project.

        Returns:
            A CLIResult with success status and message about the operation.

        """
        # Create a new project with a root node
        project = ProjectFactory.build(root_node=NodeFactory.build(id='_binder', title=title, card=card or ''))

        # Save the project, which will create the _binder.md file
        self.repository.save_project(project)

        return CLIResult(success=True, message=[f"Project '{title}' initialized successfully."])

    def get_project_info(self) -> CLIResult:
        """Get information about the current project.

        Returns:
            A CLIResult with success status and lines of text with project information.

        """
        project = self.repository.load_project()
        # Try to read the card file for the root node
        card_content = self.repository.storage.read('_binder card')
        if not card_content:  # pragma: no cover
            card_content = project.root_node.card

        lines = [
            f'Project: {project.title}\n',
            f'Description: {card_content}\n',
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
        card: str = '',
        text: str = '',
        notes: str = '',
        position: int | None = None,
    ) -> CLIResult:
        """Add a new node to the project.

        Args:
            parent_id: The ID of the parent node.
            title: The title of the new node.
            card: Brief summary of the node.
            text: Main content of the node.
            notes: Additional notes about the node.
            position: Position to insert the node.

        Returns:
            A CLIResult with success status and message about the operation.

        """
        project = self.repository.load_project()

        node = project.create_node(
            parent_id=parent_id,
            title=title,
            card=card,
            text=text,
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
        if node.card:  # pragma: no branch
            lines.extend((
                'Card:\n',
                node.card.rstrip(),
                '\n\n',
            ))

        if node.text:  # pragma: no branch
            lines.extend((
                'Text:\n',
                node.text.rstrip(),
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
            node.card = updated_node.card
            node.notes = updated_node.notes
            node.text = updated_node.text
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

    def create_card(
        self, node_id: NodeID, text: str | None = None, color: str | None = None, status: str | None = None
    ) -> CLIResult:
        """Create a card for a node.

        Args:
            node_id: ID of the node to create a card for.
            text: Initial text for the card.
            color: Color code for the card.
            status: Status label for the card.

        Returns:
            A CLIResult with success status and message.

        """
        try:
            project = self.repository.load_project()
            node = project.get_node_by_id(node_id)

            if not node:  # pragma: no cover
                return CLIResult(success=False, message=[f"Node with ID '{node_id}' not found"])

            if node.card:
                return CLIResult(
                    success=False, message=[f"Node '{node_id}' already has a card. Use 'pmk card edit' to modify it."]
                )

            # Create the card with provided options
            node.card = text or ''

            # Store color and status in metadata if provided
            if color or status:  # pragma: no cover
                if 'card' not in node.metadata:
                    node.metadata['card'] = {}

                if color:
                    node.metadata['card']['color'] = color
                if status:
                    node.metadata['card']['status'] = status

            # Save the project
            self.repository.save_node(node)

            return CLIResult(success=True, message=[f"Created card for node '{node_id}' ({node.title})."])

        except (OSError, ValueError, TypeError) as e:  # pragma: no cover
            return CLIResult(success=False, message=[f'Error creating card: {e!s}'])

    def prepare_card_for_editor(self, node_id: NodeID) -> CLIResult:
        """Prepare a node's card for editing in an external editor.

        Args:
            node_id: ID of the node whose card will be edited.

        Returns:
            A CLIResult with success status and the card content.

        """
        try:
            project = self.repository.load_project()
            node = project.get_node_by_id(node_id)

            if not node:  # pragma: no cover
                return CLIResult(success=False, message=[f"Node with ID '{node_id}' not found"])

            if not node.card:  # pragma: no cover
                # Initialize with empty card
                card_content = ''

                # Add metadata header if available
                if 'card' in node.metadata:
                    card_metadata = node.metadata['card']
                    card_content = '---\n'
                    for key, value in card_metadata.items():
                        card_content += f'{key}: {value}\n'
                    card_content += '---\n\n'
            else:
                # Start with existing card content
                card_content = node.card

                # Add metadata header if available and not already present
                if 'card' in node.metadata and not card_content.startswith('---'):  # pragma: no cover
                    card_metadata = node.metadata['card']
                    header = '---\n'
                    for key, value in card_metadata.items():
                        header += f'{key}: {value}\n'
                    header += '---\n\n'
                    card_content = header + card_content

            return CLIResult(
                success=True, message=[f"Editing card for node '{node_id}' ({node.title})."], data=card_content
            )

        except (OSError, ValueError, TypeError) as e:  # pragma: no cover
            return CLIResult(success=False, message=[f'Error preparing card for editor: {e!s}'])

    def edit_card(self, node_id: NodeID, edited_content: str) -> CLIResult:
        """Save edited card content for a node.

        Args:
            node_id: ID of the node whose card was edited.
            edited_content: The edited card content.

        Returns:
            A CLIResult with success status and message.

        """
        try:
            project = self.repository.load_project()
            node = project.get_node_by_id(node_id)

            if not node:  # pragma: no cover
                return CLIResult(success=False, message=[f"Node with ID '{node_id}' not found"])

            # Check for YAML frontmatter
            import re

            import yaml

            frontmatter_match = re.match(r'^---\n(.*?)\n---\n(.*)', edited_content, re.DOTALL)
            if frontmatter_match:
                # Extract frontmatter and content
                frontmatter_text = frontmatter_match.group(1)
                card_content = frontmatter_match.group(2).strip()

                try:
                    # Parse frontmatter as YAML
                    frontmatter = yaml.safe_load(frontmatter_text)
                    if frontmatter and isinstance(frontmatter, dict):  # pragma: no branch
                        if 'card' not in node.metadata:  # pragma: no cover
                            node.metadata['card'] = {}
                        node.metadata['card'].update(frontmatter)
                except yaml.YAMLError:  # pragma: no cover
                    # If YAML parsing fails, treat it as part of the content
                    card_content = edited_content
            else:
                # No frontmatter, use entire content
                card_content = edited_content

            # Update the card content
            node.card = card_content

            # Save the node
            self.repository.save_node(node)

            return CLIResult(success=True, message=[f"Updated card for node '{node_id}' ({node.title})."])

        except (OSError, ValueError, TypeError, ImportError) as e:  # pragma: no cover
            return CLIResult(success=False, message=[f'Error saving card: {e!s}'])

    def show_card(self, node_id: NodeID) -> CLIResult:
        """Display a node's card content.

        Args:
            node_id: ID of the node whose card will be displayed.

        Returns:
            A CLIResult with success status and the card content.

        """
        try:
            project = self.repository.load_project()
            node = project.get_node_by_id(node_id)

            if not node:  # pragma: no cover
                return CLIResult(success=False, message=[f"Node with ID '{node_id}' not found"])

            if not node.card:  # pragma: no cover
                return CLIResult(success=False, message=[f"Node '{node_id}' ({node.title}) does not have a card."])

            # Format the card display
            output = [f'Card for: {node.title} ({node_id})\n']

            # Add metadata if available
            if 'card' in node.metadata:
                card_metadata = node.metadata['card']
                if card_metadata:  # pragma: no branch
                    output.append('Metadata:')
                    for key, value in card_metadata.items():
                        output.append(f'  {key}: {value}')
                    output.append('')

            # Add the card content
            output.extend(('Content:', node.card))

            return CLIResult(success=True, message=output)

        except (OSError, ValueError, TypeError, ImportError) as e:  # pragma: no cover
            return CLIResult(success=False, message=[f'Error showing card: {e!s}'])

    def _collect_nodes_with_cards(self, node: Node) -> list[Node]:
        """Recursively collect all nodes with cards starting from the given node."""
        nodes_with_cards = []
        if node.card:  # pragma: no branch
            nodes_with_cards.append(node)
        for child in node.children:
            nodes_with_cards.extend(self._collect_nodes_with_cards(child))
        return nodes_with_cards

    def _format_cards_json(self, nodes_with_cards: list[Node]) -> str:
        """Format the list of nodes with cards as a JSON string."""
        import json

        card_data = []
        for node in nodes_with_cards:
            card_info = {'id': node.id, 'title': node.title, 'content': node.card}
            if 'card' in node.metadata:  # pragma: no cover
                card_info['metadata'] = node.metadata['card']
            card_data.append(card_info)
        return json.dumps(card_data, indent=2)

    def _format_cards_text(self, nodes_with_cards: list[Node]) -> list[str]:
        """Format the list of nodes with cards as a list of text lines."""
        output = [f'Found {len(nodes_with_cards)} cards:\n']
        for node in nodes_with_cards:
            node_line = f'- {node.title} ({node.id})'
            if 'card' in node.metadata and 'status' in node.metadata['card']:  # pragma: no cover
                node_line += f' [Status: {node.metadata["card"]["status"]}]'
            output.append(node_line)
            if node.card:  # pragma: no branch
                preview = node.card.split('\n')[0]
                if len(preview) > 60:  # pragma: no cover
                    preview = preview[:57] + '...'
                output.append(f'  {preview}')
        return output

    def list_cards(self, format_type: str = 'text') -> CLIResult:
        """List all nodes with cards.

        Args:
            format_type: Output format ('text' or 'json').

        Returns:
            A CLIResult with success status and the list of cards.

        """
        try:
            project = self.repository.load_project()
            nodes_with_cards = self._collect_nodes_with_cards(project.root_node)

            if not nodes_with_cards:  # pragma: no cover
                return CLIResult(success=True, message=['No cards found in the project.'])

            if format_type == 'json':
                return CLIResult(success=True, message=[self._format_cards_json(nodes_with_cards)])
            # text format
            return CLIResult(success=True, message=self._format_cards_text(nodes_with_cards))

        except (OSError, ValueError, TypeError, ImportError) as e:  # pragma: no cover
            return CLIResult(success=False, message=[f'Error listing cards: {e!s}'])

    def remove_card(self, node_id: NodeID) -> CLIResult:
        """Remove a node's card.

        Args:
            node_id: ID of the node whose card will be removed.

        Returns:
            A CLIResult with success status and message.

        """
        try:
            project = self.repository.load_project()
            node = project.get_node_by_id(node_id)

            if not node:  # pragma: no cover
                return CLIResult(success=False, message=[f"Node with ID '{node_id}' not found"])

            if not node.card and ('card' not in node.metadata or not node.metadata['card']):
                return CLIResult(success=False, message=[f"Node '{node_id}' ({node.title}) does not have a card."])

            # Remove the card content
            node.card = ''

            # Remove card metadata if present
            if 'card' in node.metadata:  # pragma: no cover
                del node.metadata['card']

            # Delete the card file from storage
            self.repository.storage.delete(f'{node.id} card')

            # Optionally, also delete notes file if you want to clean up when card is removed
            self.repository.storage.delete(f'{node.id} notes')

            # Save the node
            self.repository.save_node(node)

            return CLIResult(success=True, message=[f"Removed card from node '{node_id}' ({node.title})."])

        except (OSError, ValueError, TypeError) as e:  # pragma: no cover
            return CLIResult(success=False, message=[f'Error removing card: {e!s}'])
