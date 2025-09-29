"""Unit tests for PlaceholderService."""

import pytest

from prosemark.templates.domain.entities.placeholder import Placeholder
from prosemark.templates.domain.services.placeholder_service import PlaceholderService
from prosemark.templates.domain.values.placeholder_pattern import PlaceholderPattern


class TestPlaceholderService:
    """Test PlaceholderService domain service."""

    def test_extract_placeholders_from_text_simple(self) -> None:
        """Test extracting placeholders from simple text."""
        service = PlaceholderService()
        text = 'Hello {{name}}, welcome to {{project}}!'

        placeholders = service.extract_placeholders_from_text(text)

        assert len(placeholders) == 2
        placeholder_names = {p.name for p in placeholders}
        assert placeholder_names == {'name', 'project'}

    def test_extract_placeholders_from_text_with_frontmatter(self) -> None:
        """Test extracting placeholders from text with frontmatter context."""
        service = PlaceholderService()

        # Simulate full template content
        text = """---
title: "{{title}}"
author: "{{author}}"
author_default: "Anonymous"
description_default: "No description"
---

# {{title}}

Written by {{author}}.

{{description}}
"""

        frontmatter = {
            'title': '{{title}}',
            'author': '{{author}}',
            'author_default': 'Anonymous',
            'description_default': 'No description',
        }

        placeholders = service.extract_placeholders_from_text(text, frontmatter)

        assert len(placeholders) == 3
        placeholder_names = {p.name for p in placeholders}
        assert placeholder_names == {'title', 'author', 'description'}

        # Check required vs optional based on defaults
        title_placeholder = next(p for p in placeholders if p.name == 'title')
        author_placeholder = next(p for p in placeholders if p.name == 'author')
        description_placeholder = next(p for p in placeholders if p.name == 'description')

        assert title_placeholder.required is True  # No default
        assert author_placeholder.required is False  # Has default
        assert author_placeholder.default_value == 'Anonymous'
        assert description_placeholder.required is False  # Has default
        assert description_placeholder.default_value == 'No description'

    def test_extract_placeholders_no_duplicates(self) -> None:
        """Test that duplicate placeholders are not created."""
        service = PlaceholderService()
        text = '{{name}} and {{name}} again, plus {{title}} and {{name}} once more'

        placeholders = service.extract_placeholders_from_text(text)

        assert len(placeholders) == 2
        placeholder_names = {p.name for p in placeholders}
        assert placeholder_names == {'name', 'title'}

    def test_extract_placeholders_empty_text(self) -> None:
        """Test extracting placeholders from empty text."""
        service = PlaceholderService()

        placeholders = service.extract_placeholders_from_text('')
        assert len(placeholders) == 0

    def test_extract_placeholders_no_placeholders(self) -> None:
        """Test extracting placeholders when none exist."""
        service = PlaceholderService()
        text = 'This is just regular text with no placeholders.'

        placeholders = service.extract_placeholders_from_text(text)
        assert len(placeholders) == 0

    def test_extract_placeholders_invalid_patterns(self) -> None:
        """Test that invalid placeholder patterns are ignored."""
        service = PlaceholderService()
        text = 'Valid: {{name}}, Invalid: {single}, Invalid: {{{triple}}}, Invalid: {{invalid-dash}}'

        placeholders = service.extract_placeholders_from_text(text)

        assert len(placeholders) == 1
        assert placeholders[0].name == 'name'

    def test_validate_placeholder_pattern_valid(self) -> None:
        """Test validating valid placeholder patterns."""
        service = PlaceholderService()

        valid_patterns = ['{{title}}', '{{author}}', '{{project_name}}', '{{description123}}', '{{_private}}']

        for pattern in valid_patterns:
            assert service.validate_placeholder_pattern(pattern) is True

    def test_validate_placeholder_pattern_invalid(self) -> None:
        """Test validating invalid placeholder patterns."""
        service = PlaceholderService()

        invalid_patterns = [
            '{title}',  # Single braces
            '{{{title}}}',  # Triple braces
            '{{title-name}}',  # Hyphen not allowed
            '{{123title}}',  # Cannot start with number
            '{{}}',  # Empty
            'title',  # No braces
            '{{title name}}',  # Space not allowed
            '{{title.name}}',  # Dot not allowed
        ]

        for pattern in invalid_patterns:
            assert service.validate_placeholder_pattern(pattern) is False

    def test_get_placeholder_names_from_text(self) -> None:
        """Test extracting just the placeholder names from text."""
        service = PlaceholderService()
        text = 'Hello {{name}}, your {{role}} in {{project}} is important!'

        names = service.get_placeholder_names_from_text(text)

        assert names == {'name', 'role', 'project'}

    def test_get_placeholder_names_from_text_empty(self) -> None:
        """Test extracting placeholder names from empty text."""
        service = PlaceholderService()

        names = service.get_placeholder_names_from_text('')
        assert names == set()

    def test_replace_placeholders_in_text(self) -> None:
        """Test replacing placeholders in text with values."""
        service = PlaceholderService()
        text = 'Hello {{name}}, welcome to {{project}}!'
        values = {'name': 'Alice', 'project': 'MyProject'}

        result = service.replace_placeholders_in_text(text, values)

        assert result == 'Hello Alice, welcome to MyProject!'

    def test_replace_placeholders_partial_replacement(self) -> None:
        """Test replacing placeholders when only some values are provided."""
        service = PlaceholderService()
        text = 'Hello {{name}}, welcome to {{project}} on {{date}}!'
        values = {
            'name': 'Alice',
            'project': 'MyProject',
            # date is missing
        }

        result = service.replace_placeholders_in_text(text, values)

        assert result == 'Hello Alice, welcome to MyProject on {{date}}!'

    def test_replace_placeholders_no_values(self) -> None:
        """Test replacing placeholders with no values provided."""
        service = PlaceholderService()
        text = 'Hello {{name}}, welcome to {{project}}!'

        result = service.replace_placeholders_in_text(text, {})

        assert result == 'Hello {{name}}, welcome to {{project}}!'

    def test_replace_placeholders_extra_values(self) -> None:
        """Test replacing placeholders with extra values that don't match."""
        service = PlaceholderService()
        text = 'Hello {{name}}!'
        values = {'name': 'Alice', 'extra': 'value', 'unused': 'data'}

        result = service.replace_placeholders_in_text(text, values)

        assert result == 'Hello Alice!'

    def test_create_placeholder_from_pattern(self) -> None:
        """Test creating placeholder from pattern string."""
        service = PlaceholderService()
        pattern = '{{title}}'
        frontmatter = {'title': '{{title}}', 'title_description': 'The document title'}

        placeholder = service.create_placeholder_from_pattern(pattern, frontmatter)

        assert placeholder.name == 'title'
        assert placeholder.pattern == '{{title}}'
        assert placeholder.required is True
        assert placeholder.description == 'The document title'

    def test_create_placeholder_from_pattern_with_default(self) -> None:
        """Test creating placeholder from pattern with default value."""
        service = PlaceholderService()
        pattern = '{{author}}'
        frontmatter = {
            'author': '{{author}}',
            'author_default': 'Anonymous',
            'author_description': 'The document author',
        }

        placeholder = service.create_placeholder_from_pattern(pattern, frontmatter)

        assert placeholder.name == 'author'
        assert placeholder.required is False
        assert placeholder.default_value == 'Anonymous'
        assert placeholder.description == 'The document author'

    def test_create_placeholder_from_pattern_minimal(self) -> None:
        """Test creating placeholder with minimal frontmatter."""
        service = PlaceholderService()
        pattern = '{{content}}'
        frontmatter = {}

        placeholder = service.create_placeholder_from_pattern(pattern, frontmatter)

        assert placeholder.name == 'content'
        assert placeholder.required is True
        assert placeholder.default_value is None
        assert placeholder.description is None

    def test_merge_placeholder_lists_no_conflicts(self) -> None:
        """Test merging placeholder lists with no conflicts."""
        service = PlaceholderService()

        list1 = [
            Placeholder(
                name='title',
                pattern_obj=PlaceholderPattern('{{title}}'),
                required=True,
                default_value=None,
                description=None,
            )
        ]

        list2 = [
            Placeholder(
                name='author',
                pattern_obj=PlaceholderPattern('{{author}}'),
                required=False,
                default_value='Anonymous',
                description=None,
            )
        ]

        merged = service.merge_placeholder_lists([list1, list2])

        assert len(merged) == 2
        names = {p.name for p in merged}
        assert names == {'title', 'author'}

    def test_merge_placeholder_lists_with_conflicts(self) -> None:
        """Test merging placeholder lists with conflicts raises error."""
        service = PlaceholderService()

        # Same name but different requirements
        placeholder1 = Placeholder(
            name='author',
            pattern_obj=PlaceholderPattern('{{author}}'),
            required=True,
            default_value=None,
            description=None,
        )

        placeholder2 = Placeholder(
            name='author',
            pattern_obj=PlaceholderPattern('{{author}}'),
            required=False,
            default_value='Anonymous',
            description=None,
        )

        list1 = [placeholder1]
        list2 = [placeholder2]

        with pytest.raises(ValueError, match='Conflicting placeholder definitions'):
            service.merge_placeholder_lists([list1, list2])

    def test_merge_placeholder_lists_identical(self) -> None:
        """Test merging identical placeholders (should deduplicate)."""
        service = PlaceholderService()

        placeholder = Placeholder(
            name='title',
            pattern_obj=PlaceholderPattern('{{title}}'),
            required=True,
            default_value=None,
            description=None,
        )

        list1 = [placeholder]
        list2 = [placeholder]

        merged = service.merge_placeholder_lists([list1, list2])

        assert len(merged) == 1
        assert merged[0].name == 'title'
