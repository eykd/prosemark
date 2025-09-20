"""YAML frontmatter codec for parsing and generating frontmatter blocks."""

import re
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
    FRONTMATTER_PATTERN = re.compile(r'^---\r?\n(.*?)\r?\n---\r?\n(.*?)$', re.DOTALL | re.MULTILINE)

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
        # Check if content starts with frontmatter
        match = self.FRONTMATTER_PATTERN.match(content)
        if not match:
            return {}, content

        yaml_content = match.group(1)
        remaining_content = match.group(2)

        try:
            # Use safe_load to prevent code execution
            frontmatter_data = yaml.safe_load(yaml_content)

            # Handle empty frontmatter
            if frontmatter_data is None:
                frontmatter_data = {}

            # Ensure we got a dict
            if not isinstance(frontmatter_data, dict):
                raise FrontmatterFormatError('Frontmatter must be a YAML mapping/dictionary')
        except yaml.YAMLError as exc:
            raise FrontmatterFormatError('Invalid YAML in frontmatter block') from exc
        else:
            return frontmatter_data, remaining_content

    def generate(self, frontmatter: dict[str, Any], content: str) -> str:
        """Generate markdown content with frontmatter block.

        Args:
            frontmatter: Dictionary of frontmatter data
            content: Markdown content to append after frontmatter

        Returns:
            Complete markdown content with frontmatter block

        """
        if not frontmatter:
            return content

        try:
            # Generate YAML with consistent formatting
            yaml_content = yaml.safe_dump(
                frontmatter, default_flow_style=False, allow_unicode=True, sort_keys=True
            ).strip()
        except yaml.YAMLError as exc:
            raise FrontmatterFormatError('Failed to serialize frontmatter to YAML') from exc
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
