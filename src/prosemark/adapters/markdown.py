"""Markdown file adapter for project persistence.

This module provides an implementation of the ProjectRepository interface
that uses Markdown files for storage.
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from prosemark.domain.nodes import Node
from prosemark.domain.projects import Project
from prosemark.domain.repositories import ProjectRepository


class MarkdownFileAdapter(ProjectRepository):
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
        if not self.base_path.exists():
            self.base_path.mkdir(parents=True)
        elif not self.base_path.is_dir():
            raise ValueError(f'Base path {base_path} exists but is not a directory')

    def save(self, project: Project) -> None:
        """Save a project to the repository.

        Args:
            project: The project to save.

        Raises:
            OSError: If there's an error writing to the filesystem.

        """
        project_dir = self.base_path / project.name

        # Create project directory if it doesn't exist
        if not project_dir.exists():
            project_dir.mkdir(parents=True)

        # Save project metadata
        metadata_path = project_dir / 'project.json'
        with open(metadata_path, 'w', encoding='utf-8') as f:
            json.dump(
                {
                    'name': project.name,
                    'description': project.description,
                    'root_node_id': project.root_node.id,
                    'metadata': project.metadata,
                },
                f,
                indent=2,
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

        # Prepare the node content
        content = self._node_to_markdown(node)

        # Write the node file
        with open(node_path, 'w', encoding='utf-8') as f:
            f.write(content)

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
        lines.append(f'id: {node.id}')
        lines.append(f'title: {node.title}')

        # Add children IDs if any
        if node.children:
            lines.append('children:')
            for child in node.children:
                lines.append(f'  - {child.id}')

        # Add any custom metadata
        if node.metadata:
            lines.append('metadata:')
            for key, value in node.metadata.items():
                lines.append(f'  {key}: {json.dumps(value)}')

        lines.append('---')

        # Add notecard as a blockquote
        if node.notecard:
            lines.append('\n> ' + node.notecard.replace('\n', '\n> '))

        # Add main content
        if node.content:
            lines.append('\n' + node.content)

        # Add notes in a section
        if node.notes:
            lines.append('\n## Notes\n')
            lines.append(node.notes)

        return '\n'.join(lines)

    def load(self, project_id: str) -> Project:
        """Load a project from the repository.

        Args:
            project_id: The identifier of the project to load.

        Returns:
            The loaded project.

        Raises:
            ValueError: If the project cannot be found.
            OSError: If there's an error reading from the filesystem.

        """
        project_dir = self.base_path / project_id

        if not project_dir.exists() or not project_dir.is_dir():
            raise ValueError(f'Project {project_id} not found')

        # Load project metadata
        metadata_path = project_dir / 'project.json'
        if not metadata_path.exists():
            raise ValueError(f'Project metadata file not found for {project_id}')

        with open(metadata_path, encoding='utf-8') as f:
            project_data = json.load(f)

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
            # Load the root node and all its children
            nodes_by_id: dict[str, Node] = {}

            # First pass: load all nodes without setting parent-child relationships
            for node_file in project_dir.glob('*.md'):
                if node_file.name == 'project.json':
                    continue

                node = self._markdown_to_node(node_file)
                nodes_by_id[node.id] = node

            # Second pass: set up parent-child relationships
            for node_file in project_dir.glob('*.md'):
                if node_file.name == 'project.json':
                    continue

                node_id, child_ids = self._extract_node_relationships(node_file)
                if node_id in nodes_by_id:
                    node = nodes_by_id[node_id]
                    for child_id in child_ids:
                        if child_id in nodes_by_id:
                            child_node = nodes_by_id[child_id]
                            # Only add if not already a child
                            if child_node not in node.children:
                                node.add_child(child_node)

            # Set the root node
            if root_node_id in nodes_by_id:
                project.root_node = nodes_by_id[root_node_id]

        return project

    def _markdown_to_node(self, file_path: Path) -> Node:
        """Convert a Markdown file to a Node.

        Args:
            file_path: Path to the Markdown file.

        Returns:
            A Node object.

        Raises:
            ValueError: If the file cannot be parsed.
            OSError: If there's an error reading from the filesystem.

        """
        with open(file_path, encoding='utf-8') as f:
            content = f.read()

        # Extract YAML frontmatter
        frontmatter_match = re.match(r'---\n(.*?)\n---', content, re.DOTALL)
        if not frontmatter_match:
            raise ValueError(f'Invalid Markdown file format: {file_path}')

        frontmatter = frontmatter_match.group(1)

        # Parse frontmatter
        node_id = None
        title = ''
        metadata: dict[str, Any] = {}

        for line in frontmatter.split('\n'):
            if line.startswith('id:'):
                node_id = line.split(':', 1)[1].strip()
            elif line.startswith('title:'):
                title = line.split(':', 1)[1].strip()
            elif line.startswith('metadata:'):
                # Skip the metadata line itself, we'll parse the nested items
                continue
            elif line.startswith('  ') and ':' in line and not line.startswith('  -'):
                # This is a metadata item
                key, value_str = line.strip().split(':', 1)
                try:
                    value = json.loads(value_str.strip())
                    metadata[key] = value
                except json.JSONDecodeError:
                    metadata[key] = value_str.strip()

        # Remove frontmatter from content
        content_without_frontmatter = content[frontmatter_match.end():]

        # Extract notecard (first blockquote)
        notecard = ''
        notecard_match = re.search(r'\n>(.*?)(?=\n[^>]|\Z)', content_without_frontmatter, re.DOTALL)
        if notecard_match:
            notecard_text = notecard_match.group(1)
            # Remove the '> ' prefix from each line
            notecard = '\n'.join(line.lstrip('> ').strip() for line in notecard_text.split('\n'))
            # Remove the notecard from content
            content_without_frontmatter = content_without_frontmatter.replace(notecard_match.group(0), '', 1)

        # Extract notes section
        notes = ''
        notes_match = re.search(r'\n## Notes\n(.*?)(?=\n##|\Z)', content_without_frontmatter, re.DOTALL)
        if notes_match:
            notes = notes_match.group(1).strip()
            # Remove the notes section from content
            content_without_frontmatter = content_without_frontmatter.replace(notes_match.group(0), '', 1)

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

    def _extract_node_relationships(self, file_path: Path) -> tuple[str, list[str]]:
        """Extract node ID and child IDs from a Markdown file.

        Args:
            file_path: Path to the Markdown file.

        Returns:
            A tuple containing the node ID and a list of child IDs.

        Raises:
            ValueError: If the file cannot be parsed.
            OSError: If there's an error reading from the filesystem.

        """
        with open(file_path, encoding='utf-8') as f:
            content = f.read()

        # Extract YAML frontmatter
        frontmatter_match = re.match(r'---\n(.*?)\n---', content, re.DOTALL)
        if not frontmatter_match:
            raise ValueError(f'Invalid Markdown file format: {file_path}')

        frontmatter = frontmatter_match.group(1)

        # Parse node ID and children
        node_id = ''
        child_ids: list[str] = []

        in_children_section = False
        for line in frontmatter.split('\n'):
            if line.startswith('id:'):
                node_id = line.split(':', 1)[1].strip()
            elif line.startswith('children:'):
                in_children_section = True
            elif in_children_section and line.startswith('  -'):
                child_id = line.split('-', 1)[1].strip()
                child_ids.append(child_id)
            elif in_children_section and not line.startswith('  '):
                in_children_section = False

        return node_id, child_ids

    def list_projects(self) -> list[dict[str, str]]:
        """List all available projects in the repository.

        Returns:
            A list of dictionaries containing project metadata.
            Each dictionary contains 'id' and 'name' keys.

        Raises:
            OSError: If there's an error reading from the filesystem.

        """
        projects = []

        # Iterate through directories in the base path
        for item in self.base_path.iterdir():
            if item.is_dir():
                # Check if this is a project directory (has a project.json file)
                metadata_path = item / 'project.json'
                if metadata_path.exists():
                    try:
                        with open(metadata_path, encoding='utf-8') as f:
                            project_data = json.load(f)
                            projects.append({
                                'id': item.name,
                                'name': project_data.get('name', item.name),
                            })
                    except (json.JSONDecodeError, OSError):
                        # If we can't read the metadata, just use the directory name
                        projects.append({
                            'id': item.name,
                            'name': item.name,
                        })

        return projects

    def create_project(self, name: str, description: str = '') -> Project:
        """Create a new project in the repository.

        Args:
            name: The name of the new project.
            description: An optional description of the project.

        Returns:
            The newly created project.

        Raises:
            ValueError: If a project with the same name already exists.
            OSError: If there's an error writing to the filesystem.

        """
        project_dir = self.base_path / name

        # Check if project already exists
        if project_dir.exists():
            raise ValueError(f'Project {name} already exists')

        # Create the project
        project = Project(name=name, description=description)

        # Save it
        self.save(project)

        return project

    def delete_project(self, project_id: str) -> None:
        """Delete a project from the repository.

        Args:
            project_id: The identifier of the project to delete.

        Raises:
            ValueError: If the project cannot be found.
            OSError: If there's an error deleting the project.

        """
        project_dir = self.base_path / project_id

        if not project_dir.exists() or not project_dir.is_dir():
            raise ValueError(f'Project {project_id} not found')

        # Delete all files in the project directory
        for item in project_dir.iterdir():
            if item.is_file():
                item.unlink()

        # Delete the project directory
        project_dir.rmdir()
