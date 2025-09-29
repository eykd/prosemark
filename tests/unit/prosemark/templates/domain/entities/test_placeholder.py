"""Unit tests for Placeholder entity."""

import pytest

from prosemark.templates.domain.entities.placeholder import Placeholder
from prosemark.templates.domain.exceptions.template_exceptions import InvalidPlaceholderValueError
from prosemark.templates.domain.values.placeholder_pattern import PlaceholderPattern


class TestPlaceholder:
    """Test Placeholder entity creation and behavior."""

    def test_create_required_placeholder(self) -> None:
        """Test creating a required placeholder."""
        pattern = PlaceholderPattern('{{title}}')
        placeholder = Placeholder(
            name='title', pattern_obj=pattern, required=True, default_value=None, description=None
        )

        assert placeholder.name == 'title'
        assert placeholder.pattern == '{{title}}'
        assert placeholder.required is True
        assert placeholder.default_value is None
        assert placeholder.description is None

    def test_create_optional_placeholder_with_default(self) -> None:
        """Test creating an optional placeholder with default value."""
        pattern = PlaceholderPattern('{{author}}')
        placeholder = Placeholder(
            name='author',
            pattern_obj=pattern,
            required=False,
            default_value='Anonymous',
            description='The article author',
        )

        assert placeholder.name == 'author'
        assert placeholder.pattern == '{{author}}'
        assert placeholder.required is False
        assert placeholder.default_value == 'Anonymous'
        assert placeholder.description == 'The article author'

    def test_get_effective_value_with_provided_value(self) -> None:
        """Test getting effective value when value is provided."""
        pattern = PlaceholderPattern('{{title}}')
        placeholder = Placeholder(
            name='title', pattern_obj=pattern, required=True, default_value=None, description=None
        )

        effective_value = placeholder.get_effective_value('My Title')
        assert effective_value == 'My Title'

    def test_get_effective_value_with_default(self) -> None:
        """Test getting effective value using default."""
        pattern = PlaceholderPattern('{{author}}')
        placeholder = Placeholder(
            name='author', pattern_obj=pattern, required=False, default_value='Anonymous', description=None
        )

        effective_value = placeholder.get_effective_value()
        assert effective_value == 'Anonymous'

    def test_get_effective_value_required_no_value_raises_error(self) -> None:
        """Test that required placeholder without value raises error."""
        pattern = PlaceholderPattern('{{title}}')
        placeholder = Placeholder(
            name='title', pattern_obj=pattern, required=True, default_value=None, description=None
        )

        with pytest.raises(InvalidPlaceholderValueError, match='Missing value for required placeholder: title'):
            placeholder.get_effective_value()

    def test_get_effective_value_required_empty_string_raises_error(self) -> None:
        """Test that required placeholder with empty string raises error."""
        pattern = PlaceholderPattern('{{title}}')
        placeholder = Placeholder(
            name='title', pattern_obj=pattern, required=True, default_value=None, description=None
        )

        with pytest.raises(InvalidPlaceholderValueError, match='Empty value for required placeholder: title'):
            placeholder.get_effective_value('')

    def test_get_effective_value_required_whitespace_raises_error(self) -> None:
        """Test that required placeholder with whitespace-only value raises error."""
        pattern = PlaceholderPattern('{{title}}')
        placeholder = Placeholder(
            name='title', pattern_obj=pattern, required=True, default_value=None, description=None
        )

        with pytest.raises(InvalidPlaceholderValueError, match='Empty value for required placeholder: title'):
            placeholder.get_effective_value('   ')

    def test_validate_value_valid(self) -> None:
        """Test validating a valid placeholder value."""
        pattern = PlaceholderPattern('{{title}}')
        placeholder = Placeholder(
            name='title', pattern_obj=pattern, required=True, default_value=None, description=None
        )

        # Should not raise any exception
        placeholder.validate_value('Valid Title')

    def test_validate_value_required_empty_raises_error(self) -> None:
        """Test validating empty value for required placeholder."""
        pattern = PlaceholderPattern('{{title}}')
        placeholder = Placeholder(
            name='title', pattern_obj=pattern, required=True, default_value=None, description=None
        )

        with pytest.raises(InvalidPlaceholderValueError, match='Empty value for required placeholder: title'):
            placeholder.validate_value('')

    def test_validate_value_optional_empty_allowed(self) -> None:
        """Test validating empty value for optional placeholder."""
        pattern = PlaceholderPattern('{{description}}')
        placeholder = Placeholder(
            name='description', pattern_obj=pattern, required=False, default_value='No description', description=None
        )

        # Should not raise any exception
        placeholder.validate_value('')

    def test_placeholder_equality(self) -> None:
        """Test placeholder equality comparison."""
        pattern1 = PlaceholderPattern('{{title}}')
        pattern2 = PlaceholderPattern('{{title}}')
        pattern3 = PlaceholderPattern('{{author}}')

        placeholder1 = Placeholder(
            name='title', pattern_obj=pattern1, required=True, default_value=None, description=None
        )

        placeholder2 = Placeholder(
            name='title', pattern_obj=pattern2, required=True, default_value=None, description=None
        )

        placeholder3 = Placeholder(
            name='author', pattern_obj=pattern3, required=False, default_value='Anonymous', description=None
        )

        assert placeholder1 == placeholder2
        assert placeholder1 != placeholder3
        assert placeholder2 != placeholder3

    def test_placeholder_string_representation(self) -> None:
        """Test placeholder string representation."""
        pattern = PlaceholderPattern('{{title}}')
        placeholder = Placeholder(
            name='title', pattern_obj=pattern, required=True, default_value=None, description='The document title'
        )

        str_repr = str(placeholder)
        assert "Placeholder(name='title'" in str_repr
        assert 'required=True' in str_repr

    def test_placeholder_hash(self) -> None:
        """Test placeholder hash for use in sets and dicts."""
        pattern1 = PlaceholderPattern('{{title}}')
        pattern2 = PlaceholderPattern('{{title}}')

        placeholder1 = Placeholder(
            name='title', pattern_obj=pattern1, required=True, default_value=None, description=None
        )

        placeholder2 = Placeholder(
            name='title', pattern_obj=pattern2, required=True, default_value=None, description=None
        )

        # Equal placeholders should have same hash
        assert hash(placeholder1) == hash(placeholder2)

        # Should be usable in sets
        placeholder_set = {placeholder1, placeholder2}
        assert len(placeholder_set) == 1  # Should deduplicate

    def test_from_frontmatter_required(self) -> None:
        """Test creating placeholder from frontmatter (required)."""
        frontmatter = {'title': '{{title}}'}
        pattern = PlaceholderPattern('{{title}}')

        placeholder = Placeholder.from_frontmatter('title', frontmatter, pattern)

        assert placeholder.name == 'title'
        assert placeholder.required is True
        assert placeholder.default_value is None
        assert placeholder.description is None

    def test_from_frontmatter_with_default(self) -> None:
        """Test creating placeholder from frontmatter with default."""
        frontmatter = {'author': '{{author}}', 'author_default': 'Anonymous'}
        pattern = PlaceholderPattern('{{author}}')

        placeholder = Placeholder.from_frontmatter('author', frontmatter, pattern)

        assert placeholder.name == 'author'
        assert placeholder.required is False
        assert placeholder.default_value == 'Anonymous'
        assert placeholder.description is None

    def test_from_frontmatter_with_description(self) -> None:
        """Test creating placeholder from frontmatter with description."""
        frontmatter = {'title': '{{title}}', 'title_description': 'The document title'}
        pattern = PlaceholderPattern('{{title}}')

        placeholder = Placeholder.from_frontmatter('title', frontmatter, pattern)

        assert placeholder.name == 'title'
        assert placeholder.required is True
        assert placeholder.default_value is None
        assert placeholder.description == 'The document title'

    def test_from_frontmatter_with_default_and_description(self) -> None:
        """Test creating placeholder from frontmatter with both default and description."""
        frontmatter = {
            'author': '{{author}}',
            'author_default': 'Anonymous',
            'author_description': 'The document author',
        }
        pattern = PlaceholderPattern('{{author}}')

        placeholder = Placeholder.from_frontmatter('author', frontmatter, pattern)

        assert placeholder.name == 'author'
        assert placeholder.required is False
        assert placeholder.default_value == 'Anonymous'
        assert placeholder.description == 'The document author'
