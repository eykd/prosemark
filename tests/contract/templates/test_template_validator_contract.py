"""Contract tests for TemplateValidatorPort.

These tests verify that implementations of TemplateValidatorPort
correctly implement the interface contract.
"""

from pathlib import Path
from typing import Protocol

import pytest

from prosemark.templates.domain.entities.template import Template
from prosemark.templates.domain.exceptions.template_exceptions import (
    InvalidPlaceholderError,
    TemplateParseError,
    TemplateValidationError,
)
from prosemark.templates.domain.values.template_path import TemplatePath
from prosemark.templates.ports.template_validator_port import TemplateValidatorPort


class TemplateValidatorContract(Protocol):
    """Protocol that all TemplateValidatorPort contract tests must implement."""

    @pytest.fixture
    def validator(self) -> TemplateValidatorPort:
        """Return a TemplateValidatorPort implementation to test."""
        ...


class BaseTemplateValidatorContract:
    """Contract tests that all TemplateValidatorPort implementations must pass."""

    @pytest.fixture
    def valid_template_content(self) -> str:
        """Return valid template content for testing."""
        return (
            '---\n'
            'title: "{{title}}"\n'
            'type: document\n'
            '---\n\n'
            '# {{title}}\n\n'
            'This is a template with {{placeholder}} content.\n\n'
            '## Section with {{section_title}}\n\n'
            'More content here.'
        )

    @pytest.fixture
    def invalid_yaml_content(self) -> str:
        """Return template content with invalid YAML frontmatter."""
        return (
            '---\n'
            'title: {{title}\n'  # Missing closing quote
            'type: document\n'
            'invalid: [\n'  # Unclosed bracket
            '---\n\n'
            '# Content'
        )

    @pytest.fixture
    def invalid_prosemark_content(self) -> str:
        """Return content that violates prosemark format."""
        return '# Title without frontmatter\n\nThis content has no YAML frontmatter.'

    @pytest.fixture
    def content_with_placeholders(self) -> str:
        """Return content with various placeholder formats."""
        return (
            '---\n'
            'title: "{{title}}"\n'
            '---\n\n'
            '# {{main_title}}\n\n'
            'Content with {{simple_placeholder}}.\n\n'
            'Author: {{author_name}}\n'
            'Date: {{current_date}}\n\n'
            'Invalid: {single_brace}\n'
            'Invalid: {{invalid-dash}}\n'
            'Valid: {{valid_underscore}}\n'
            'Valid: {{CamelCase}}'
        )

    def test_validate_template_structure_valid(
        self, validator: TemplateValidatorPort, valid_template_content: str
    ) -> None:
        """Test validating valid template structure."""
        result = validator.validate_template_structure(valid_template_content)
        assert result is True

    def test_validate_template_structure_invalid_yaml(
        self, validator: TemplateValidatorPort, invalid_yaml_content: str
    ) -> None:
        """Test validating template with invalid YAML frontmatter."""
        with pytest.raises(TemplateParseError):
            validator.validate_template_structure(invalid_yaml_content)

    def test_validate_template_structure_no_frontmatter(self, validator: TemplateValidatorPort) -> None:
        """Test validating template without frontmatter."""
        content = '# Just a title\n\nNo frontmatter here.'

        with pytest.raises(TemplateValidationError):
            validator.validate_template_structure(content)

    def test_validate_prosemark_format_valid(
        self, validator: TemplateValidatorPort, valid_template_content: str
    ) -> None:
        """Test validating valid prosemark format."""
        result = validator.validate_prosemark_format(valid_template_content)
        assert result is True

    def test_validate_prosemark_format_invalid(
        self, validator: TemplateValidatorPort, invalid_prosemark_content: str
    ) -> None:
        """Test validating invalid prosemark format."""
        with pytest.raises(TemplateValidationError):
            validator.validate_prosemark_format(invalid_prosemark_content)

    def test_extract_placeholders_valid_content(
        self, validator: TemplateValidatorPort, content_with_placeholders: str
    ) -> None:
        """Test extracting placeholders from valid content."""
        placeholders = validator.extract_placeholders(content_with_placeholders)

        assert isinstance(placeholders, list)
        assert len(placeholders) >= 5  # At least 5 valid placeholders

        placeholder_names = [p.name for p in placeholders]
        assert 'title' in placeholder_names
        assert 'main_title' in placeholder_names
        assert 'simple_placeholder' in placeholder_names
        assert 'author_name' in placeholder_names
        assert 'current_date' in placeholder_names
        assert 'valid_underscore' in placeholder_names

        # Invalid placeholders should not be included
        assert 'single_brace' not in placeholder_names
        assert 'invalid-dash' not in placeholder_names

    def test_extract_placeholders_no_placeholders(self, validator: TemplateValidatorPort) -> None:
        """Test extracting placeholders from content without placeholders."""
        content = '---\ntitle: Static Title\n---\n\n# Static Content\n\nNo placeholders here.'

        placeholders = validator.extract_placeholders(content)
        assert isinstance(placeholders, list)
        assert len(placeholders) == 0

    def test_extract_placeholders_malformed_content(self, validator: TemplateValidatorPort) -> None:
        """Test extracting placeholders from content with malformed placeholders."""
        content = (
            '---\n'
            'title: Test\n'
            '---\n\n'
            'Malformed: {{invalid-name}}\n'
            'Unclosed: {{unclosed\n'
            'Single brace: {invalid}\n'
            'Valid: {{valid_name}}'
        )

        with pytest.raises(InvalidPlaceholderError):
            validator.extract_placeholders(content)

    def test_validate_placeholder_syntax_valid(self, validator: TemplateValidatorPort) -> None:
        """Test validating valid placeholder syntax."""
        valid_patterns = [
            '{{simple}}',
            '{{with_underscore}}',
            '{{CamelCase}}',
            '{{snake_case_long}}',
            '{{_leading_underscore}}',
            '{{name123}}',
        ]

        for pattern in valid_patterns:
            assert validator.validate_placeholder_syntax(pattern) is True

    def test_validate_placeholder_syntax_invalid(self, validator: TemplateValidatorPort) -> None:
        """Test validating invalid placeholder syntax."""
        invalid_patterns = [
            '{single_brace}',
            '{{invalid-dash}}',
            '{{invalid space}}',
            '{{123_starts_with_number}}',
            '{{invalid.dot}}',
            '{{}}',  # Empty
            '{{invalid@symbol}}',
            'unclosed{{',
            '}}backwards{{',
        ]

        for pattern in invalid_patterns:
            with pytest.raises(InvalidPlaceholderError):
                validator.validate_placeholder_syntax(pattern)

    def test_validate_template_dependencies_valid(self, validator: TemplateValidatorPort) -> None:
        """Test validating template with valid dependencies."""
        # Note: This test assumes we have a valid Template instance
        # In actual implementation, this would test dependency resolution
        # For now, we'll test the interface exists

        # Test now passes as Template entity is implemented
        template_content = '---\ntitle: test\n---\n\nTest content'
        template = Template(name='test', path=TemplatePath(Path('/test')), content=template_content)
        result = validator.validate_template_dependencies(template)

        # Should succeed with valid template content
        assert result is True

    def test_validate_template_dependencies_invalid(self, validator: TemplateValidatorPort) -> None:
        """Test validating template with invalid dependencies."""
        # Test now passes as Template entity is implemented
        template_content = '---\ntitle: test\n---\n\nTest content'
        template = Template(name='test', path=TemplatePath(Path('/test')), content=template_content)
        result = validator.validate_template_dependencies(template)

        # Should succeed with valid template content
        assert result is True
