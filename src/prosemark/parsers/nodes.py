"""Node parser implementation.

This module provides the NodeParser class which is responsible for parsing
node files with YAML headers and special directives.
"""

from __future__ import annotations

import re
from typing import Any

import yaml


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
            'notecard': '',
            'content': '',
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
                    if 'id' in header_data:
                        node_data['id'] = header_data.pop('id')
                    if 'title' in header_data:
                        node_data['title'] = header_data.pop('title')
                    # Store remaining header data as metadata
                    node_data['metadata'].update(header_data)

                # Remove the header from content
                remaining_content = content[header_match.end():]
            except yaml.YAMLError:
                # If YAML parsing fails, treat everything as content
                remaining_content = content
        else:
            # No header found, treat everything as content
            remaining_content = content

        # Process directives and extract content
        content_lines, directives = cls.process_directives(remaining_content)

        # Update node data with directives
        for key, value in directives.items():
            if key.lower() == 'notecard':
                node_data['notecard'] = value
            elif key.lower() == 'notes':
                node_data['notes'] = value
            else:
                # Store other directives in metadata
                node_data['metadata'][key] = value

        # Set the content
        node_data['content'] = '\n'.join(content_lines).strip()

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
        for i, line in enumerate(lines):
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
        notecard = node_data.get('notecard', '')
        notes = node_data.get('notes', '')
        content = node_data.get('content', '')
        metadata = node_data.get('metadata', {})

        # Create YAML header
        header_data = {'id': node_id, 'title': title}
        header_data.update(metadata)

        # Generate YAML header
        yaml_header = yaml.dump(header_data, default_flow_style=False, sort_keys=False)

        # Build the full content
        lines = ['---', yaml_header.rstrip(), '---']

        # Add directives
        if notecard:
            lines.append(f'// Notecard: {notecard}')
        else:
            lines.append(f'// Notecard: [[{node_id} notecard.md]]')

        if notes:
            lines.append(f'// Notes: {notes}')
        else:
            lines.append(f'// Notes: [[{node_id} notes.md]]')

        # Add a blank line before content
        lines.append('')

        # Add content if present
        if content:
            lines.append(content)

        return '\n'.join(lines)
