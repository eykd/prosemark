"""Markdown file adapter for project persistence.

This module provides an implementation of the ProjectRepository interface
that uses Markdown files for storage.
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any, cast

from prosemark.domain.nodes import Node
from prosemark.domain.projects import Project
from prosemark.storages.repositories.base import ProjectRepository
from prosemark.storages.repositories.exceptions import ProjectExistsError, ProjectNotFoundError


class MarkdownFilesystemProjectRepository(ProjectRepository):
    """A ProjectRepository implementation that uses Markdown files for storage.

    This adapter stores projects as a directory structure with Markdown files.
    Each node in the project is represented by a separate Markdown file.
    """

    def __init__(self, base_path: str | Path) -> None:
        """Initialize the adapter with a base directory for storage.

        Args:
            base_path: The directory where projects will be stored.
                If the directory doesn't exist, it will be created.

        Raises:
            ValueError: If the base_path exists but is not a directory.

        """
        self.base_path = Path(base_path)

        # Create the base directory if it doesn't exist
        if not self.base_path.exists():  # pragma: no branch
            self.base_path.mkdir(parents=True)
        elif not self.base_path.is_dir():
            msg = f'Base path {base_path} exists but is not a directory'
            raise ValueError(msg)

    def save(self, project: Project) -> None:
        """Save the project to the repository.

        Args:
            project: The project to save.

        Raises:
            OSError: If there's an error writing to the filesystem.

        """
        project_dir = self.base_path

        # Ensure the directory exists
        if not project_dir.exists():  # pragma: no cover
            project_dir.mkdir(parents=True)

        # Save project metadata
        metadata_path = project_dir / 'project.json'
        metadata_path.write_text(
            json.dumps(
                {
                    'name': project.name,
                    'description': project.description,
                    'root_node_id': project.root_node.id,
                    'metadata': project.metadata,
                },
                indent=2,
            ),
            encoding='utf-8',
        )

        # Save all nodes
        self._save_node(project.root_node, project_dir)

    def _save_node(self, node: Node, project_dir: Path) -> None:
        """Save a node and its children to the filesystem.

        Args:
            node: The node to save.
            project_dir: The project directory.

        Raises:
            OSError: If there's an error writing to the filesystem.

        """
        # Create a safe filename from the node ID
        filename = f'{node.id}.md'
        node_path = project_dir / filename

        # Save notes to a separate file if they exist
        if node.notes:
            notes_filename = f'{node.id} notes.md'
            notes_path = project_dir / notes_filename
            notes_path.write_text(node.notes, encoding='utf-8')

        # Save notecard to a separate file if it exists
        if node.notecard:
            notecard_filename = f'{node.id} notecard.md'
            notecard_path = project_dir / notecard_filename
            notecard_path.write_text(node.notecard, encoding='utf-8')

        # Prepare the node content
        content = self._node_to_markdown(node)

        # Write the node file
        node_path.write_text(content, encoding='utf-8')

        # Save all children
        for child in node.children:
            self._save_node(child, project_dir)

    def _node_to_markdown(self, node: Node) -> str:
        """Convert a node to Markdown format.

        Args:
            node: The node to convert.

        Returns:
            A string containing the Markdown representation of the node.

        """
        # Start with YAML frontmatter for metadata
        lines = ['---']
        lines.extend([f'id: {node.id}', f'title: {node.title}'])

        # Add children IDs if any
        if node.children:
            lines.append('children:')
            lines.extend([f'  - {child.id}' for child in node.children])

        # Add reference to notes file if notes exist
        if node.notes:
            lines.append(f'notes_file: {node.id} notes.md')

        # Add reference to notecard file if notecard exists
        if node.notecard:
            lines.append(f'notecard_file: {node.id} notecard.md')

        # Add any custom metadata
        if node.metadata:
            lines.append('metadata:')
            lines.extend([f'  {key}: {json.dumps(value)}' for key, value in node.metadata.items()])

        lines.append('---')

        # Add main content
        if node.content:
            lines.append('\n' + node.content)

        # Notes and notecard are now in separate files, so we don't include them here

        return '\n'.join(lines)

    def _load_project_metadata(self, project_dir: Path) -> dict[str, Any]:
        """Load project metadata from the project directory.

        Args:
            project_dir: The project directory.

        Returns:
            A dictionary containing the project metadata.

        Raises:
            ProjectNotFoundError: If the project metadata file cannot be found.

        """
        metadata_path = project_dir / 'project.json'
        if not metadata_path.exists():  # pragma: no cover
            raise ProjectNotFoundError
        return cast('dict[str, Any]', json.loads(metadata_path.read_text(encoding='utf-8')))

    def _load_nodes(self, project_dir: Path) -> dict[str, Node]:
        """Load all nodes from the project directory.

        Args:
            project_dir: The project directory.

        Returns:
            A dictionary mapping node IDs to Node objects.

        """
        nodes_by_id: dict[str, Node] = {}
        for node_file in project_dir.glob('*.md'):
            # Skip project.json, notes files, and notecard files
            if (
                node_file.name == 'project.json' or ' notes.md' in node_file.name or ' notecard.md' in node_file.name
            ):  # pragma: no cover
                continue

            # Convert file to node
            node = self._markdown_to_node(node_file)

            # Only add to dictionary if node was successfully created
            if node is not None:  # pragma: no branch
                nodes_by_id[node.id] = node
        return nodes_by_id

    def _setup_node_relationships(self, project_dir: Path, nodes_by_id: dict[str, Node]) -> None:
        """Set up parent-child relationships between nodes.

        Args:
            project_dir: The project directory.
            nodes_by_id: A dictionary mapping node IDs to Node objects.

        """
        for node_file in project_dir.glob('*.md'):
            # Skip project.json, notes files, and notecard files
            if (
                node_file.name == 'project.json' or ' notes.md' in node_file.name or ' notecard.md' in node_file.name
            ):  # pragma: no cover
                continue

            # Extract node relationships
            node_id, child_ids = self._extract_node_relationships(node_file)

            # Skip if node_id is None (invalid frontmatter)
            if node_id is None:  # pragma: no cover
                continue

            if node_id in nodes_by_id:  # pragma: no branch
                node = nodes_by_id[node_id]
                for child_id in child_ids:
                    if child_id in nodes_by_id:  # pragma: no branch
                        child_node = nodes_by_id[child_id]
                        if child_node not in node.children:  # pragma: no branch
                            node.add_child(child_node)

    def load(self) -> Project:
        """Load the project from the repository.

        Returns:
            The loaded project.

        Raises:
            ProjectNotFoundError: If the project cannot be found.
            OSError: If there's an error reading from the filesystem.

        """
        project_dir = self.base_path

        # Check if project.json exists
        metadata_path = project_dir / 'project.json'
        if not metadata_path.exists():
            raise ProjectNotFoundError

        project_data = self._load_project_metadata(project_dir)

        # Create the project without a root node first
        project = Project(
            name=project_data['name'],
            description=project_data.get('description', ''),
            metadata=project_data.get('metadata', {}),
        )

        # Load the root node and all its children
        root_node_id = project_data.get('root_node_id')
        if not root_node_id:
            # If no root node ID is specified, use the project name as the root node title
            project.root_node.title = project.name
        else:
            nodes_by_id = self._load_nodes(project_dir)
            self._setup_node_relationships(project_dir, nodes_by_id)
            if root_node_id in nodes_by_id:  # pragma: no branch
                project.root_node = nodes_by_id[root_node_id]

        return project

    def _markdown_to_node(self, file_path: Path) -> Node | None:  # noqa: C901
        """Convert a Markdown file to a Node.

        Args:
            file_path: Path to the Markdown file.

        Returns:
            A Node object or None if the file doesn't have valid frontmatter.

        Raises:
            OSError: If there's an error reading from the filesystem.

        """
        content = Path(file_path).read_text(encoding='utf-8')

        # Extract YAML frontmatter
        frontmatter_match = re.match(r'---\n(.*?)\n---', content, re.DOTALL)
        if not frontmatter_match:
            # Instead of raising an error, just return None to ignore this file
            return None

        frontmatter = frontmatter_match.group(1)

        # Parse frontmatter
        node_id = None
        title = ''
        metadata: dict[str, Any] = {}
        notes_file = None
        notecard_file = None

        for line in frontmatter.split('\n'):  # pragma: no branch
            if line.startswith('id:'):
                node_id = line.split(':', 1)[1].strip()
            elif line.startswith('title:'):
                title = line.split(':', 1)[1].strip()
            elif line.startswith('notes_file:'):
                notes_file = line.split(':', 1)[1].strip()
            elif line.startswith('notecard_file:'):
                notecard_file = line.split(':', 1)[1].strip()
            elif line.startswith('metadata:'):
                # Skip the metadata line itself, we'll parse the nested items
                continue
            elif line.startswith('  ') and ':' in line and not line.startswith('  -'):
                # This is a metadata item
                key, value_str = line.strip().split(':', 1)
                try:
                    value = json.loads(value_str.strip())
                    metadata[key] = value
                except json.JSONDecodeError:  # pragma: no cover
                    metadata[key] = value_str.strip()

        # Remove frontmatter from content
        content_without_frontmatter = content[frontmatter_match.end() :]

        # Load notes from separate file if it exists
        notes = ''
        if notes_file:
            notes_path = file_path.parent / notes_file
            if notes_path.exists():  # pragma: no branch
                notes = notes_path.read_text(encoding='utf-8')

        # Load notecard from separate file if it exists
        notecard = ''
        if notecard_file:
            notecard_path = file_path.parent / notecard_file
            if notecard_path.exists():  # pragma: no branch
                notecard = notecard_path.read_text(encoding='utf-8')

        # The remaining content is the main content
        main_content = content_without_frontmatter.strip()

        return Node(
            node_id=node_id,
            title=title,
            notecard=notecard,
            content=main_content,
            notes=notes,
            metadata=metadata,
        )

    def _extract_node_relationships(self, file_path: Path) -> tuple[str | None, list[str]]:
        """Extract node ID and child IDs from a Markdown file.

        Args:
            file_path: Path to the Markdown file.

        Returns:
            A tuple containing the node ID and a list of child IDs, or (None, []) if frontmatter is missing.

        Raises:
            OSError: If there's an error reading from the filesystem.

        """
        content = Path(file_path).read_text(encoding='utf-8')

        # Extract YAML frontmatter
        frontmatter_match = re.match(r'---\n(.*?)\n---', content, re.DOTALL)
        if not frontmatter_match:
            # Instead of raising an error, return None for node_id and empty list for child_ids
            return None, []

        frontmatter = frontmatter_match.group(1)

        # Parse node ID and children
        node_id = ''
        child_ids: list[str] = []

        in_children_section = False
        for line in frontmatter.split('\n'):  # pragma: no branch
            if line.startswith('id:'):
                node_id = line.split(':', 1)[1].strip()
            elif line.startswith('children:'):
                in_children_section = True
            elif in_children_section and line.startswith('  -'):
                child_id = line.split('-', 1)[1].strip()
                child_ids.append(child_id)
            elif in_children_section and not line.startswith('  '):  # pragma: no cover
                in_children_section = False

        return node_id, child_ids

    def exists(self) -> bool:
        """Check if a project exists in the repository.

        Returns:
            True if a project exists, False otherwise.

        """
        metadata_path = self.base_path / 'project.json'
        return metadata_path.exists()

    def create(self, name: str, description: str = '') -> Project:
        """Create a new project in the repository.

        Args:
            name: The name of the new project.
            description: An optional description of the project.

        Returns:
            The newly created project.

        Raises:
            ProjectExistsError: If a project already exists in the repository.
            OSError: If there's an error writing to the filesystem.

        """
        if self.exists():
            raise ProjectExistsError

        # Create the project
        project = Project(name=name, description=description)

        # Save it
        self.save(project)

        return project

    def delete(self) -> None:
        """Delete the project from the repository.

        Raises:
            ProjectNotFoundError: If the project cannot be found.
            OSError: If there's an error deleting the project.

        """
        project_dir = self.base_path
        metadata_path = project_dir / 'project.json'

        if not metadata_path.exists():
            raise ProjectNotFoundError

        # Delete all markdown files in the directory
        for item in project_dir.glob('*.md'):
            if item.is_file():  # pragma: no branch
                item.unlink()

        # Delete the project.json file
        metadata_path.unlink()

    def parse_edit_markdown(self, markdown: str) -> dict[str, str]:  # noqa: C901
        """Parse markdown content from the edit command.

        Args:
            markdown: The markdown content to parse.

        Returns:
            A dictionary containing the parsed sections (title, notecard, content, notes).

        """
        sections: dict[str, str] = {}
        current_section = None
        section_content: list[str] = []

        for line in markdown.split('\n'):  # pragma: no branch
            if line.startswith('# Title:'):
                # Extract title directly from this line
                title_value = line.replace('# Title:', '').strip()
                # Always add title to sections, even if empty
                sections['title'] = title_value
                current_section = 'title'
                section_content = []
            elif line.startswith('# Notecard'):
                if current_section and section_content and current_section != 'title':  # pragma: no cover
                    sections[current_section] = '\n'.join(section_content).strip()
                current_section = 'notecard'
                section_content = []
            elif line.startswith('# Content'):
                if current_section and section_content:  # pragma: no branch
                    sections[current_section] = '\n'.join(section_content).strip()
                current_section = 'content'
                section_content = []
            elif line.startswith('# Notes'):
                if current_section and section_content:  # pragma: no branch
                    sections[current_section] = '\n'.join(section_content).strip()
                current_section = 'notes'
                section_content = []
            elif line.startswith('# Instructions:'):
                if current_section and section_content:  # pragma: no branch
                    sections[current_section] = '\n'.join(section_content).strip()
                break
            elif not line.startswith('#'):  # pragma: no branch
                section_content.append(line)

        # Save the last section
        if current_section and section_content:  # pragma: no branch
            sections[current_section] = '\n'.join(section_content).strip()

        return sections

    def generate_edit_markdown(self, node: Node) -> str:
        """Generate markdown content for the edit command.

        Args:
            node: The node to generate markdown for.

        Returns:
            A string containing the markdown content.

        """
        lines = [
            f'# Title: {node.title}\n',
            '# Notecard (brief summary):',
            f'{node.notecard}\n',
            '# Content (main text):',
            f'{node.content}\n',
            '# Notes (additional information):',
            f'{node.notes}\n',
            '# Instructions:',
            '# Edit the content above. Lines starting with # are comments and will be ignored.\n',
        ]
        return '\n'.join(lines)

    def update_node(
        self,
        node: Node,
        title: str | None = None,
        notecard: str | None = None,
        content: str | None = None,
        notes: str | None = None,
    ) -> Node:
        """Update a node's content.

        Args:
            node: The node to update.
            title: New title for the node.
            notecard: New notecard for the node.
            content: New content for the node.
            notes: New notes for the node.

        """
        # Update fields provided via options
        if title is not None:
            node.title = title
        if notecard is not None:
            node.notecard = notecard
        if content is not None:
            node.content = content
        if notes is not None:
            node.notes = notes

        return node
