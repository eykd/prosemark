# Copyright (c) 2024 Prosemark Contributors
# This software is licensed under the MIT License

"""YAML frontmatter codec for parsing and generating frontmatter blocks."""

import re
from datetime import datetime
from typing import Any

import yaml

from prosemark.exceptions import FrontmatterFormatError


class FrontmatterCodec:
    """YAML frontmatter codec for parsing and generating frontmatter blocks.

    This adapter handles the encoding and decoding of YAML frontmatter in markdown files.
    It provides safe parsing and generation of frontmatter blocks with proper error handling
    and format validation.

    Supported frontmatter format:
    ```
    ---
    key: value
    other_key: other_value
    ---
    (content)
    ```

    The codec ensures:
    - Safe YAML parsing (no arbitrary code execution)
    - Consistent frontmatter block formatting
    - Proper error handling for malformed YAML
    - Round-trip compatibility (parse -> generate -> parse)
    """

    # Regex pattern to match frontmatter block at start of content
    FRONTMATTER_PATTERN = re.compile(r'^---\r?\n(.*?)\r?\n---(?:\r?\n(.*))?$', re.DOTALL)

    def parse(self, content: str) -> tuple[dict[str, Any], str]:
        """Parse frontmatter and content from markdown text.

        Args:
            content: Raw markdown content with optional frontmatter

        Returns:
            Tuple of (frontmatter_dict, remaining_content)
            If no frontmatter is found, returns ({}, original_content)

        Raises:
            FrontmatterFormatError: If frontmatter YAML is malformed

        """
        # Validate frontmatter format
        self._validate_frontmatter_format(content)

        # Check if content starts with frontmatter
        match = self.FRONTMATTER_PATTERN.match(content)
        if not match:
            return {}, content

        yaml_content = match.group(1)
        remaining_content = match.group(2) or ''

        # Remove leading newline from content if present
        if remaining_content:
            remaining_content = remaining_content.removeprefix('\n')

        # Parse YAML content
        frontmatter_data = FrontmatterCodec._parse_yaml_content(yaml_content)
        return frontmatter_data, remaining_content

    @staticmethod
    def generate(frontmatter: dict[str, Any], content: str) -> str:
        """Generate markdown content with frontmatter block.

        Args:
            frontmatter: Dictionary of frontmatter data
            content: Markdown content to append after frontmatter

        Returns:
            Complete markdown content with frontmatter block

        Raises:
            FrontmatterFormatError: If YAML serialization fails

        """
        if not frontmatter:
            return content

        try:
            # Generate YAML with consistent formatting
            yaml_content = yaml.safe_dump(
                frontmatter,
                default_flow_style=False,
                allow_unicode=True,
                sort_keys=True,
                default_style='',
            ).strip()
        except yaml.YAMLError as exc:
            msg = 'Failed to serialize frontmatter to YAML'
            raise FrontmatterFormatError(msg) from exc
        else:
            return f'---\n{yaml_content}\n---\n{content}'

    def update_frontmatter(self, content: str, updates: dict[str, Any]) -> str:
        """Update frontmatter in existing content.

        Args:
            content: Existing markdown content with or without frontmatter
            updates: Dictionary of frontmatter updates to apply

        Returns:
            Updated markdown content with modified frontmatter

        """
        # Parse existing frontmatter
        existing_frontmatter, remaining_content = self.parse(content)

        # Merge updates
        updated_frontmatter = {**existing_frontmatter, **updates}

        # Generate new content
        return self.generate(updated_frontmatter, remaining_content)

    def _validate_frontmatter_format(self, content: str) -> None:
        """Validate frontmatter format and raise errors for malformed patterns.

        Raises:
            FrontmatterFormatError: If frontmatter delimiters are malformed

        """
        if content.startswith('---') and not self.FRONTMATTER_PATTERN.match(content):
            if '---' not in content[3:]:
                msg = 'Frontmatter block missing closing delimiter'
                raise FrontmatterFormatError(msg)
        elif '---' in content and not content.startswith('---'):
            FrontmatterCodec._check_misplaced_frontmatter(content)

    @staticmethod
    def _check_misplaced_frontmatter(content: str) -> None:
        """Check for frontmatter that is not at the document start.

        Raises:
            FrontmatterFormatError: If frontmatter delimiters found in wrong position

        """
        lines = content.split('\n')
        for i, line in enumerate(lines):
            if line.strip() == '---':
                if i > 0 and any(
                    'id:' in prev_line or 'title:' in prev_line or 'created:' in prev_line for prev_line in lines[:i]
                ):
                    msg = 'Frontmatter block missing opening delimiter'
                    raise FrontmatterFormatError(msg)
                if i < len(lines) - 1 and lines[i + 1].strip() == '---':
                    msg = 'Frontmatter block not at document start'
                    raise FrontmatterFormatError(msg)
                break

    @staticmethod
    def _parse_yaml_content(yaml_content: str) -> dict[str, Any]:
        """Parse YAML content and return processed frontmatter data.

        Returns:
            Parsed frontmatter data as dictionary

        Raises:
            FrontmatterFormatError: If YAML parsing fails or data is invalid

        """
        try:
            frontmatter_data = yaml.safe_load(yaml_content)

            if frontmatter_data is None:
                frontmatter_data = {}

            if not isinstance(frontmatter_data, dict):
                msg = 'Frontmatter must be a YAML mapping/dictionary'
                raise FrontmatterFormatError(msg)

            return FrontmatterCodec._convert_datetimes_to_strings(frontmatter_data)

        except yaml.YAMLError as exc:
            msg = 'Invalid YAML in frontmatter block'
            raise FrontmatterFormatError(msg) from exc

    @staticmethod
    def _convert_datetimes_to_strings(data: dict[str, Any]) -> dict[str, Any]:
        """Convert datetime objects to ISO format strings to preserve original format.

        YAML automatically parses ISO timestamp strings to datetime objects,
        but we want to preserve them as strings in frontmatter for human readability.

        Args:
            data: Dictionary that may contain datetime objects

        Returns:
            Dictionary with datetime objects converted to ISO strings

        """
        result = {}
        for key, value in data.items():
            if isinstance(value, datetime):
                # Convert datetime to ISO string with Z suffix (UTC)
                result[key] = value.strftime('%Y-%m-%dT%H:%M:%SZ')
            else:
                result[key] = value
        return result
