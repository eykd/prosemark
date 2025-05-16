"""Node parser implementation.

This module provides the NodeParser class which is responsible for parsing
node files with YAML headers and special directives.
"""

from __future__ import annotations

import re
from typing import TYPE_CHECKING, Any

import yaml

if TYPE_CHECKING:  # pragma: no cover
    from prosemark.domain.nodes import Node


class NodeParser:
    """Parser for node files with YAML headers and special directives.

    This class provides methods to parse node files with YAML-style headers
    and special directives, and to serialize node data back to text.
    """

    # Regular expressions for parsing
    YAML_HEADER_PATTERN = re.compile(r'^---\s*\n(.*?)\n---\s*\n', re.DOTALL)
    DIRECTIVE_PATTERN = re.compile(r'^//\s*(.*?):\s*(.*?)\s*$')

    @classmethod
    def parse(cls, content: str, node_id: str = '') -> dict[str, Any]:
        """Parse node content into a structured dictionary.

        Args:
            content: The content of the node file.
            node_id: The ID of the node (used as fallback if not in content).

        Returns:
            A dictionary containing the parsed node data.

        """
        # Initialize with default values
        node_data: dict[str, Any] = {
            'id': node_id,
            'title': '',
            'card': '',
            'text': '',
            'notes': '',
            'metadata': {},
        }

        if not content:
            return node_data

        # Extract YAML header if present
        header_match = cls.YAML_HEADER_PATTERN.match(content)
        if header_match:
            yaml_content = header_match.group(1)
            try:
                header_data = yaml.safe_load(yaml_content) or {}
                if isinstance(header_data, dict):
                    # Update node data with header values
                    if 'id' in header_data:  # pragma: no branch
                        node_data['id'] = header_data.pop('id')
                    if 'title' in header_data:  # pragma: no branch
                        node_data['title'] = header_data.pop('title')
                    # Store remaining header data as metadata
                    node_data['metadata'].update(header_data)

                    # Remove the header from content
                    remaining_content = content[header_match.end() :]
                else:
                    remaining_content = content
            except yaml.YAMLError:  # pragma: no cover
                # If YAML parsing fails, treat everything as content
                remaining_content = content
        else:
            # No header found, treat everything as content
            remaining_content = content

        # Process directives and extract content
        content_lines, directives = cls.process_directives(remaining_content)

        # Update node data with directives
        for key, value in directives.items():
            if key.lower() == 'card':
                node_data['card'] = value
            elif key.lower() == 'notes':
                node_data['notes'] = value
            else:
                # Store other directives in metadata
                node_data['metadata'][key] = value

        # Set the text
        node_data['text'] = '\n'.join(content_lines).strip()

        return node_data

    @classmethod
    def process_directives(cls, content: str) -> tuple[list[str], dict[str, str]]:
        """Process directives and separate them from content.

        Args:
            content: The content to process.

        Returns:
            A tuple containing the content lines and directive dictionary.

        """
        lines = content.split('\n')
        directives = {}
        content_start_index = 0

        # Process lines that start with // as directives
        for i, line in enumerate(lines):  # pragma: no branch
            directive_match = cls.DIRECTIVE_PATTERN.match(line)
            if directive_match:
                key = directive_match.group(1).strip()
                value = directive_match.group(2).strip()
                directives[key] = value
                content_start_index = i + 1
            elif line.strip() and not line.startswith('//'):
                # First non-directive, non-empty line marks the start of content
                content_start_index = i
                break

        return lines[content_start_index:], directives

    @classmethod
    def serialize(cls, node_data: dict[str, Any]) -> str:
        """Serialize node data to text format.

        Args:
            node_data: The node data to serialize.

        Returns:
            The serialized node content.

        """
        # Extract basic properties
        node_id = node_data.get('id', '')
        title = node_data.get('title', '')
        text = node_data.get('text', '')
        metadata = node_data.get('metadata', {})

        # Create YAML header
        header_data = {'id': node_id, 'title': title}
        header_data.update(metadata)

        # Generate YAML header
        yaml_header = yaml.dump(header_data, default_flow_style=False, sort_keys=False)

        # Build the full content
        lines = ['---', yaml_header.rstrip(), '---']

        # Add directives - always use wikilink format
        lines.extend([
            f'// Card: [[{node_id} card.md]]',
            f'// Notes: [[{node_id} notes.md]]',
        ])

        # Add a blank line before text
        lines.append('')

        # Add text if present
        if text:
            lines.append(text)

        return '\n'.join(lines)

    @classmethod
    def prepare_for_editor(cls, node: Node) -> str:
        """Prepare node data for editing in an external editor.

        Args:
            node: The node to prepare for editing.

        Returns:
            A string representation suitable for editing.

        """
        # Create YAML header (simplified for editing)
        header = f'id: {node.id}\ntitle: {node.title}\n'

        # Add metadata if present
        if node.metadata:
            for key, value in node.metadata.items():  # pragma: no cover
                if key not in ('id', 'title'):
                    header += f'{key}: {value}\n'

        # Build the full content for editing
        lines = [header]

        # Add card section
        lines.append('// Card')
        if node.card:  # pragma: no branch
            lines.append(node.card)

        # Add notes section
        lines.append('\n// Notes')
        if node.notes:  # pragma: no branch
            lines.append(node.notes)

        # Add text section
        lines.append('\n// Text')
        if node.text:
            lines.append(node.text)

        return '\n'.join(lines)

    @classmethod
    def parse_from_editor(cls, node_id: str, content: str) -> Node:  # noqa: C901
        """Parse content from the editor format back into a Node.

        Args:
            node_id: The ID of the node.
            content: The content from the editor.

        Returns:
            A Node object containing the parsed data.

        """
        from prosemark.domain.nodes import Node

        if not content:
            return Node(id=node_id)

        lines = content.split('\n')

        # Initialize with default values
        title = ''
        card = ''
        text = ''
        notes = ''
        metadata: dict[str, Any] = {}

        # Parse header (everything before first section marker)
        header_lines = []
        i = 0
        while i < len(lines) and not lines[i].startswith('// '):
            if lines[i].strip():  # Skip empty lines
                header_lines.append(lines[i])
            i += 1

        # Process header lines
        for line in header_lines:
            if ':' in line:  # pragma: no branch
                key, value = line.split(':', 1)
                key = key.strip()
                value = value.strip()

                if key == 'id':
                    node_id = value
                elif key == 'title':
                    title = value
                else:
                    metadata[key] = value

        # Parse sections
        current_section = None
        section_content: list[str] = []

        while i < len(lines):
            line = lines[i]

            # Check for section markers
            if line.startswith('// Card'):
                if current_section:  # pragma: no cover
                    if current_section == 'card':
                        card = '\n'.join(section_content).strip()
                    elif current_section == 'notes':
                        notes = '\n'.join(section_content).strip()
                    elif current_section == 'text':
                        text = '\n'.join(section_content).strip()
                current_section = 'card'
                section_content = []
            elif line.startswith('// Notes'):
                if current_section:  # pragma: no branch
                    if current_section == 'card':
                        card = '\n'.join(section_content).strip()
                    elif current_section == 'notes':  # pragma: no cover
                        notes = '\n'.join(section_content).strip()
                    elif current_section == 'text':  # pragma: no cover
                        text = '\n'.join(section_content).strip()
                current_section = 'notes'
                section_content = []
            elif line.startswith('// Text'):
                if current_section:  # pragma: no branch
                    if current_section == 'card':  # pragma: no cover
                        card = '\n'.join(section_content).strip()
                    elif current_section == 'notes':  # pragma: no cover
                        notes = '\n'.join(section_content).strip()
                    elif current_section == 'text':  # pragma: no cover
                        text = '\n'.join(section_content).strip()
                current_section = 'text'
                section_content = []
            else:
                section_content.append(line)

            i += 1

        # Add the last section
        if current_section:  # pragma: no branch
            if current_section == 'card':  # pragma: no cover
                card = '\n'.join(section_content).strip()
            elif current_section == 'notes':  # pragma: no cover
                notes = '\n'.join(section_content).strip()
            elif current_section == 'text':  # pragma: no branch
                text = '\n'.join(section_content).strip()

        # Create and return the Node
        return Node(
            id=node_id,
            title=title,
            card=card,
            text=text,
            notes=notes,
            metadata=metadata,
        )
