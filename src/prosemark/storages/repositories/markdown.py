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
from prosemark.services.outline_parser import generate_outline, parse_outline
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

        # Save all nodes except the root (_binder)
        for node in (project.root_node, *project.root_node.get_descendants()):
            if node.id == '_binder':
                continue
            self._save_node(node, project_dir)

        # Save the root node as _binder.md
        binder_path = project_dir / '_binder.md'
        binder_content = self._root_node_to_binder_markdown(project)
        binder_path.write_text(binder_content, encoding='utf-8')

        # Save notes and notecard for _binder if they exist
        if project.root_node.notes:
            notes_path = project_dir / '_binder notes.md'
            notes_path.write_text(project.root_node.notes, encoding='utf-8')
        if project.root_node.notecard:
            notecard_path = project_dir / '_binder notecard.md'
            notecard_path.write_text(project.root_node.notecard, encoding='utf-8')

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

        # Add wikilink-style links to notecard and notes files
        lines.extend([
            '',
            '---',
            '',
            f'[[{node.id} notecard.md]]',
            f'[[{node.id} notes.md]]',
            '',
            '---',
            '',
        ])

        # Add main content
        if node.content:
            lines.append(node.content)

        # Notes and notecard are now in separate files, so we don't include them here

        return '\n'.join(lines)

    def _root_node_to_binder_markdown(self, project: Project) -> str:
        """Generate the _binder.md content from the project root node and structure."""
        root = project.root_node
        lines = ['---']
        lines.extend([
            'id: _binder',
            f'title: {project.name}',
        ])
        if project.description:
            lines.append(f'description: {json.dumps(project.description)}')
        # We no longer need to list children in frontmatter since the outline is the source of truth
        if root.notes:
            lines.append('notes_file: _binder notes.md')
        if root.notecard:
            lines.append('notecard_file: _binder notecard.md')
        if project.metadata:  # pragma: no cover
            lines.append('metadata:')
            lines.extend([f'  {key}: {json.dumps(value)}' for key, value in project.metadata.items()])
        lines.append('---\n')

        # Use the outline generator to create the structure
        outline = generate_outline(root)
        if outline:
            lines.append(outline)

        return '\n'.join(lines)

    def _parse_id_line(self, line: str, data: dict[str, Any]) -> None:
        data['id'] = line.split(':', 1)[1].strip()

    def _parse_title_line(self, line: str, data: dict[str, Any]) -> None:
        data['name'] = line.split(':', 1)[1].strip()

    def _parse_children_line(self, line: str, data: dict[str, Any]) -> None:
        children_str = line.split(':', 1)[1].strip()
        children = [s.strip() for s in children_str.strip('[]').split(',') if s.strip()]
        data['children'] = children

    def _parse_notes_file_line(self, line: str, data: dict[str, Any]) -> None:
        data['notes_file'] = line.split(':', 1)[1].strip()

    def _parse_notecard_file_line(self, line: str, data: dict[str, Any]) -> None:
        data['notecard_file'] = line.split(':', 1)[1].strip()

    def _parse_metadata_line(self, data: dict[str, Any]) -> None:
        data['metadata'] = {}

    def _parse_metadata_item_line(self, line: str, data: dict[str, Any]) -> None:
        key, value_str = line.strip().split(':', 1)
        try:
            value = json.loads(value_str.strip())
        except json.JSONDecodeError:
            value = value_str.strip()
        if 'metadata' in data:  # pragma: no branch
            data['metadata'][key] = value

    def _parse_frontmatter_lines(self, frontmatter: str) -> dict[str, Any]:
        """Parse the frontmatter lines into a metadata dictionary."""
        data: dict[str, Any] = {}
        for line in frontmatter.split('\n'):
            if line.startswith('id:'):
                self._parse_id_line(line, data)
            elif line.startswith('title:'):
                self._parse_title_line(line, data)
            elif line.startswith('description:'):
                self._parse_description_line(line, data)
            elif line.startswith('children:'):
                self._parse_children_line(line, data)
            elif line.startswith('notes_file:'):
                self._parse_notes_file_line(line, data)
            elif line.startswith('notecard_file:'):
                self._parse_notecard_file_line(line, data)
            elif line.startswith('metadata:'):
                self._parse_metadata_line(data)
            elif line.startswith('  ') and ':' in line and not line.startswith('  -'):
                self._parse_metadata_item_line(line, data)
        return data

    def _parse_description_line(self, line: str, data: dict[str, Any]) -> None:
        """Parse the description line, handling JSON and fallback to string."""
        value = line.split(':', 1)[1].strip()
        try:
            data['description'] = json.loads(value)
        except json.JSONDecodeError:  # pragma: no cover
            data['description'] = value

    def _load_project_metadata(self, project_dir: Path) -> dict[str, Any]:
        """Load project metadata from the _binder.md file. If missing or malformed, return empty dict."""
        binder_path = project_dir / '_binder.md'
        if not binder_path.exists():  # pragma: no cover
            return {}
        content = binder_path.read_text(encoding='utf-8')
        frontmatter_match = re.match(r'---\n(.*?)\n---', content, re.DOTALL)
        if not frontmatter_match:
            return {}
        frontmatter = frontmatter_match.group(1)
        return self._parse_frontmatter_lines(frontmatter)

    def _load_node_contents(self, project_dir: Path, node: Node) -> None:
        """Recursively load content for a node and its children.
        
        Args:
            project_dir: The project directory.
            node: The node to load content for.

        """
        # Skip the root node
        if node.id != '_binder':
            node_path = project_dir / f'{node.id}.md'
            if node_path.exists():
                # Load the node content
                node_content = self._load_node_content(node_path)
                if node_content:
                    node.content = node_content.get('content', '')
                    node.metadata = node_content.get('metadata', {})

            # Load notes if they exist
            notes_path = project_dir / f'{node.id} notes.md'
            if notes_path.exists():
                node.notes = notes_path.read_text(encoding='utf-8')

            # Load notecard if it exists
            notecard_path = project_dir / f'{node.id} notecard.md'
            if notecard_path.exists():
                node.notecard = notecard_path.read_text(encoding='utf-8')

        # Process all children recursively
        for child in node.children:
            self._load_node_contents(project_dir, child)

    def _load_node_content(self, node_path: Path) -> dict[str, Any]:
        """Load content and metadata from a node file.
        
        Args:
            node_path: Path to the node file.
            
        Returns:
            Dictionary with content and metadata.

        """
        content = node_path.read_text(encoding='utf-8')
        result: dict[str, Any] = {'content': '', 'metadata': {}}

        # Extract YAML frontmatter
        frontmatter_match = re.match(r'---\n(.*?)\n---', content, re.DOTALL)
        if not frontmatter_match:
            return result

        frontmatter = frontmatter_match.group(1)

        # Parse metadata from frontmatter
        metadata: dict[str, Any] = {}
        for line in frontmatter.split('\n'):
            if line.startswith('metadata:'):
                continue
            if line.startswith('  ') and ':' in line and not line.startswith('  -'):
                # This is a metadata item
                key, value_str = line.strip().split(':', 1)
                try:
                    value = json.loads(value_str.strip())
                    metadata[key] = value
                except json.JSONDecodeError:  # pragma: no cover
                    metadata[key] = value_str.strip()

        # Remove frontmatter from content
        content_without_frontmatter = content[frontmatter_match.end():]

        # Process content - filter out the wikilinks section
        wikilinks_pattern = r'\[\[.*? notecard\.md\]\]\n\[\[.*? notes\.md\]\]\n\n---\n\n'
        main_content = re.sub(wikilinks_pattern, '', content_without_frontmatter, flags=re.DOTALL).strip()

        result['content'] = main_content
        result['metadata'] = metadata

        return result

    def load(self) -> Project:
        """Load the project from the repository. If missing or malformed, return an empty Project."""
        project_dir = self.base_path
        binder_path = project_dir / '_binder.md'

        # If binder is missing, return empty Project
        if not binder_path.exists():
            return Project(name='', description='', root_node=Node(node_id='_binder', title=''))

        # Load project metadata from _binder.md
        project_data = self._load_project_metadata(project_dir)

        # If project_data is empty, treat as malformed and return empty Project
        if not project_data:
            return Project(name='', description='', root_node=Node(node_id='_binder', title=''))

        # Parse the outline from _binder.md to build the node structure
        binder_content = binder_path.read_text(encoding='utf-8')

        # Extract the outline part (after frontmatter)
        frontmatter_match = re.match(r'---\n(.*?)\n---\n', binder_content, re.DOTALL)
        if not frontmatter_match:
            # If no valid frontmatter, return empty project
            return Project(name='', description='', root_node=Node(node_id='_binder', title=''))

        outline_content = binder_content[frontmatter_match.end():].strip()

        # Parse the outline to create the node structure
        root_node = parse_outline(outline_content)

        # Set the root node ID and title
        root_node.id = '_binder'
        root_node.title = project_data.get('name', '')

        # Load content for each node
        self._load_node_contents(project_dir, root_node)

        # Load notes and notecard for root node if they exist
        notes_path = project_dir / '_binder notes.md'
        if notes_path.exists():
            root_node.notes = notes_path.read_text(encoding='utf-8')

        notecard_path = project_dir / '_binder notecard.md'
        if notecard_path.exists():
            root_node.notecard = notecard_path.read_text(encoding='utf-8')

        return Project(
            name=project_data.get('name', ''),
            description=project_data.get('description', ''),
            root_node=root_node,
            metadata=project_data.get('metadata', {}),
        )

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

        # Process content - filter out the wikilinks section
        # Look for a pattern like:
        # ---
        #
        # [[node_id notecard.md]]
        # [[node_id notes.md]]
        #
        # ---
        #
        # And extract only the content after the last ---

        # Find the wikilinks section and remove it
        wikilinks_pattern = r'\[\[.*? notecard\.md\]\]\n\[\[.*? notes\.md\]\]\n\n---\n\n'
        main_content = re.sub(wikilinks_pattern, '', content_without_frontmatter, flags=re.DOTALL).strip()

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
        for line in frontmatter.split('\n'):
            if line.startswith('id:'):
                node_id = line.split(':', 1)[1].strip()
            elif line.startswith('children:'):
                children_value = line.split(':', 1)[1].strip()
                if children_value.startswith('[') and children_value.endswith(']'):
                    # Inline list format: children: [id1, id2]
                    child_ids = [s.strip() for s in children_value.strip('[]').split(',') if s.strip()]
                    in_children_section = False
                else:
                    # YAML list format: children: (followed by indented - id lines)
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
        binder_path = self.base_path / '_binder.md'
        return binder_path.exists()

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
        # Create the root node as _binder
        root_node = Node(node_id='_binder', title=name)
        project = Project(name=name, description=description, root_node=root_node)
        self.save(project)
        return project

    def delete(self) -> None:
        """Delete the project from the repository.

        Raises:
            ProjectNotFoundError: If the project cannot be found.
            OSError: If there's an error deleting the project.

        """
        project_dir = self.base_path
        binder_path = project_dir / '_binder.md'
        if not binder_path.exists():
            raise ProjectNotFoundError
        # Delete all markdown files in the directory
        for item in project_dir.glob('*.md'):
            if item.is_file():  # pragma: no branch
                item.unlink()
        # Delete notes and notecard files for _binder
        notes_path = project_dir / '_binder notes.md'
        if notes_path.exists():  # pragma: no cover
            notes_path.unlink()
        notecard_path = project_dir / '_binder notecard.md'
        if notecard_path.exists():  # pragma: no cover
            notecard_path.unlink()

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
            if line.startswith('// Title:'):
                # Extract title directly from this line
                title_value = line.replace('// Title:', '').strip()
                # Always add title to sections, even if empty
                sections['title'] = title_value
                current_section = 'title'
                section_content = []
            elif line.startswith('// Notecard'):
                if current_section and section_content and current_section != 'title':  # pragma: no cover
                    sections[current_section] = '\n'.join(section_content).strip()
                current_section = 'notecard'
                section_content = []
            elif line.startswith('// Content'):
                if current_section and section_content:  # pragma: no branch
                    sections[current_section] = '\n'.join(section_content).strip()
                current_section = 'content'
                section_content = []
            elif line.startswith('// Notes'):
                if current_section and section_content:  # pragma: no branch
                    sections[current_section] = '\n'.join(section_content).strip()
                current_section = 'notes'
                section_content = []
            elif line.startswith('// Instructions:'):
                if current_section and section_content:  # pragma: no branch
                    sections[current_section] = '\n'.join(section_content).strip()
                break
            elif not line.startswith('//'):  # pragma: no branch
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
            f'// Title: {node.title}\n',
            '// Notecard (brief summary):',
            f'{node.notecard}\n',
            '// Content (main text):',
            f'{node.content}\n',
            '// Notes (additional information):',
            f'{node.notes}\n',
            '// Instructions:',
            '// Edit the content above. Lines starting with // are comments and will be ignored.\n',
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
