"""Unit tests for Placeholder entity."""

import pytest

from prosemark.templates.domain.entities.placeholder import Placeholder, PlaceholderValue
from prosemark.templates.domain.exceptions.template_exceptions import (
    InvalidPlaceholderError,
    InvalidPlaceholderValueError,
)
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

    def test_placeholder_empty_pattern_name_raises_error(self) -> None:
        """Test that placeholder with empty pattern name raises error (covers lines 35-36)."""
        # Create a mock pattern object with empty name to bypass PlaceholderPattern validation
        from unittest.mock import Mock

        pattern_obj = Mock(spec=PlaceholderPattern)
        pattern_obj.name = ''  # Empty name
        pattern_obj.raw = '{{}}'

        with pytest.raises(InvalidPlaceholderError, match='Invalid placeholder pattern'):
            Placeholder(name='', pattern_obj=pattern_obj, required=True)

    def test_placeholder_name_mismatch_raises_error(self) -> None:
        """Test that name mismatch with pattern raises error (covers lines 40-41)."""
        pattern = PlaceholderPattern('{{title}}')
        with pytest.raises(InvalidPlaceholderError, match='Placeholder name .* does not match pattern'):
            Placeholder(name='author', pattern_obj=pattern, required=True)

    def test_required_placeholder_with_default_raises_error(self) -> None:
        """Test that required placeholder with default value raises error (covers lines 45-46)."""
        pattern = PlaceholderPattern('{{title}}')
        with pytest.raises(InvalidPlaceholderError, match='Required placeholder .* cannot have a default value'):
            Placeholder(name='title', pattern_obj=pattern, required=True, default_value='default')

    def test_optional_placeholder_none_default_gets_empty_string(self) -> None:
        """Test that optional placeholder with None default gets empty string (covers line 51)."""
        pattern = PlaceholderPattern('{{author}}')
        placeholder = Placeholder(name='author', pattern_obj=pattern, required=False, default_value=None)

        # Should get empty string as default
        assert placeholder.default_value == ''

    def test_placeholder_non_string_default_raises_error(self) -> None:
        """Test that non-string default value raises error (covers lines 55-56)."""
        pattern = PlaceholderPattern('{{count}}')
        with pytest.raises(InvalidPlaceholderError, match='Default value .* must be a string'):
            Placeholder(name='count', pattern_obj=pattern, required=False, default_value=123)  # type: ignore[arg-type]

    def test_placeholder_has_default_property(self) -> None:
        """Test has_default property (covers line 61)."""
        pattern = PlaceholderPattern('{{author}}')

        # Optional with default
        placeholder_with_default = Placeholder(
            name='author', pattern_obj=pattern, required=False, default_value='Anonymous'
        )
        assert placeholder_with_default.has_default is True

        # Required without default
        pattern2 = PlaceholderPattern('{{title}}')
        placeholder_without_default = Placeholder(name='title', pattern_obj=pattern2, required=True)
        assert placeholder_without_default.has_default is False

    def test_from_name_creates_placeholder(self) -> None:
        """Test from_name class method (covers line 121)."""
        placeholder = Placeholder.from_name('title', required=True, description='The title')

        assert placeholder.name == 'title'
        assert placeholder.pattern == '{{title}}'
        assert placeholder.required is True
        assert placeholder.description == 'The title'

    def test_validate_value_non_string_raises_error(self) -> None:
        """Test validate_value with non-string value (covers lines 167-168)."""
        pattern = PlaceholderPattern('{{title}}')
        placeholder = Placeholder(name='title', pattern_obj=pattern, required=True)

        with pytest.raises(InvalidPlaceholderValueError, match='Placeholder value must be a string'):
            placeholder.validate_value(123)  # type: ignore[arg-type]


class TestPlaceholderValue:
    """Test PlaceholderValue entity creation and behavior."""

    def test_create_placeholder_value_user_input(self) -> None:
        """Test creating placeholder value from user input."""
        value = PlaceholderValue(placeholder_name='title', value='My Title', source='user_input')

        assert value.placeholder_name == 'title'
        assert value.value == 'My Title'
        assert value.source == 'user_input'

    def test_placeholder_value_empty_name_raises_error(self) -> None:
        """Test that empty placeholder name raises error (covers line 213)."""
        with pytest.raises(InvalidPlaceholderValueError, match='Placeholder name must be a non-empty string'):
            PlaceholderValue(placeholder_name='', value='test')

    def test_placeholder_value_non_string_value_raises_error(self) -> None:
        """Test that non-string value raises error (covers lines 218-219)."""
        with pytest.raises(InvalidPlaceholderValueError, match='Placeholder value must be a string'):
            PlaceholderValue(placeholder_name='title', value=123)  # type: ignore[arg-type]

    def test_placeholder_value_invalid_source_raises_error(self) -> None:
        """Test that invalid source raises error (covers lines 225-226)."""
        with pytest.raises(InvalidPlaceholderValueError, match='Invalid value source'):
            PlaceholderValue(placeholder_name='title', value='test', source='invalid_source')

    def test_placeholder_value_is_user_provided(self) -> None:
        """Test is_user_provided property (covers line 231)."""
        value = PlaceholderValue.from_user_input('title', 'Test')
        assert value.is_user_provided is True

        value_default = PlaceholderValue.from_default('title', 'Test')
        assert value_default.is_user_provided is False

    def test_placeholder_value_is_default_value(self) -> None:
        """Test is_default_value property (covers line 236)."""
        value_default = PlaceholderValue.from_default('title', 'Test')
        assert value_default.is_default_value is True

        value_user = PlaceholderValue.from_user_input('title', 'Test')
        assert value_user.is_default_value is False

    def test_placeholder_value_is_empty(self) -> None:
        """Test is_empty property (covers line 241)."""
        value_empty = PlaceholderValue(placeholder_name='title', value='')
        assert value_empty.is_empty is True

        value_whitespace = PlaceholderValue(placeholder_name='title', value='   ')
        assert value_whitespace.is_empty is True

        value_non_empty = PlaceholderValue(placeholder_name='title', value='Test')
        assert value_non_empty.is_empty is False

    def test_placeholder_value_from_default(self) -> None:
        """Test from_default class method (covers line 269)."""
        value = PlaceholderValue.from_default('author', 'Anonymous')

        assert value.placeholder_name == 'author'
        assert value.value == 'Anonymous'
        assert value.source == 'default'

    def test_placeholder_value_from_config(self) -> None:
        """Test from_config class method (covers line 283)."""
        value = PlaceholderValue.from_config('api_key', 'secret123')

        assert value.placeholder_name == 'api_key'
        assert value.value == 'secret123'
        assert value.source == 'config'

    def test_placeholder_value_matches_placeholder(self) -> None:
        """Test matches_placeholder method (covers line 295)."""
        pattern = PlaceholderPattern('{{title}}')
        placeholder = Placeholder(name='title', pattern_obj=pattern, required=True)

        value_matching = PlaceholderValue(placeholder_name='title', value='Test')
        value_not_matching = PlaceholderValue(placeholder_name='author', value='Test')

        assert value_matching.matches_placeholder(placeholder) is True
        assert value_not_matching.matches_placeholder(placeholder) is False
