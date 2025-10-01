"""Unit tests for PlaceholderPattern value object."""

import pytest

from prosemark.templates.domain.exceptions.template_exceptions import InvalidPlaceholderError
from prosemark.templates.domain.values.placeholder_pattern import PlaceholderPattern


class TestPlaceholderPatternInitialization:
    """Tests for PlaceholderPattern initialization and validation."""

    def test_init_with_valid_pattern(self) -> None:
        """Test initialization with a valid placeholder pattern."""
        pattern = PlaceholderPattern('{{variable_name}}')
        assert pattern.raw == '{{variable_name}}'
        assert pattern.name == 'variable_name'

    def test_init_with_valid_pattern_single_char(self) -> None:
        """Test initialization with single character variable name."""
        pattern = PlaceholderPattern('{{x}}')
        assert pattern.raw == '{{x}}'
        assert pattern.name == 'x'

    def test_init_with_valid_pattern_underscore_prefix(self) -> None:
        """Test initialization with underscore-prefixed variable name."""
        pattern = PlaceholderPattern('{{_private}}')
        assert pattern.raw == '{{_private}}'
        assert pattern.name == '_private'

    def test_init_with_valid_pattern_numbers(self) -> None:
        """Test initialization with numbers in variable name."""
        pattern = PlaceholderPattern('{{variable_123}}')
        assert pattern.raw == '{{variable_123}}'
        assert pattern.name == 'variable_123'

    def test_init_raises_error_for_non_string_pattern(self) -> None:
        """Test that initialization raises error for non-string pattern."""
        with pytest.raises(InvalidPlaceholderError) as exc_info:
            PlaceholderPattern(123)  # type: ignore[arg-type]

        assert 'must be a string' in str(exc_info.value)

    def test_init_raises_error_for_empty_pattern(self) -> None:
        """Test that initialization raises error for empty pattern."""
        with pytest.raises(InvalidPlaceholderError) as exc_info:
            PlaceholderPattern('')

        assert 'cannot be empty' in str(exc_info.value)

    def test_init_raises_error_for_whitespace_pattern(self) -> None:
        """Test that initialization raises error for whitespace-only pattern."""
        with pytest.raises(InvalidPlaceholderError) as exc_info:
            PlaceholderPattern('   ')

        assert 'cannot be empty' in str(exc_info.value)

    def test_init_raises_error_for_invalid_syntax_missing_braces(self) -> None:
        """Test that initialization raises error for missing braces."""
        with pytest.raises(InvalidPlaceholderError) as exc_info:
            PlaceholderPattern('variable_name')

        assert 'Invalid placeholder pattern syntax' in str(exc_info.value)

    def test_init_raises_error_for_invalid_syntax_single_braces(self) -> None:
        """Test that initialization raises error for single braces."""
        with pytest.raises(InvalidPlaceholderError) as exc_info:
            PlaceholderPattern('{variable_name}')

        assert 'Invalid placeholder pattern syntax' in str(exc_info.value)

    def test_init_raises_error_for_invalid_identifier_with_spaces(self) -> None:
        """Test that initialization raises error for spaces in identifier."""
        with pytest.raises(InvalidPlaceholderError) as exc_info:
            PlaceholderPattern('{{variable name}}')

        assert 'Invalid placeholder pattern syntax' in str(exc_info.value)

    def test_init_raises_error_for_invalid_identifier_with_hyphen(self) -> None:
        """Test that initialization raises error for hyphen in identifier."""
        with pytest.raises(InvalidPlaceholderError) as exc_info:
            PlaceholderPattern('{{variable-name}}')

        assert 'Invalid placeholder pattern syntax' in str(exc_info.value)

    def test_init_raises_error_for_invalid_identifier_starting_with_digit(self) -> None:
        """Test that initialization raises error for identifier starting with digit."""
        with pytest.raises(InvalidPlaceholderError) as exc_info:
            PlaceholderPattern('{{1variable}}')

        assert 'Invalid placeholder pattern syntax' in str(exc_info.value)


class TestPlaceholderPatternProperties:
    """Tests for PlaceholderPattern properties."""

    def test_raw_property_returns_pattern(self) -> None:
        """Test that raw property returns the full pattern."""
        pattern = PlaceholderPattern('{{my_var}}')
        assert pattern.raw == '{{my_var}}'

    def test_name_property_returns_variable_name(self) -> None:
        """Test that name property returns the variable name."""
        pattern = PlaceholderPattern('{{my_var}}')
        assert pattern.name == 'my_var'

    def test_is_valid_property_returns_true(self) -> None:
        """Test that is_valid always returns True for constructed instances."""
        pattern = PlaceholderPattern('{{variable}}')
        assert pattern.is_valid is True


class TestPlaceholderPatternMethods:
    """Tests for PlaceholderPattern instance methods."""

    def test_matches_text_returns_true_when_pattern_in_text(self) -> None:
        """Test that matches_text returns True when pattern is in text."""
        pattern = PlaceholderPattern('{{name}}')
        text = 'Hello {{name}}, welcome!'

        assert pattern.matches_text(text) is True

    def test_matches_text_returns_false_when_pattern_not_in_text(self) -> None:
        """Test that matches_text returns False when pattern is not in text."""
        pattern = PlaceholderPattern('{{name}}')
        text = 'Hello world, welcome!'

        assert pattern.matches_text(text) is False

    def test_extract_from_text_finds_all_occurrences(self) -> None:
        """Test extracting all occurrences of pattern from text."""
        pattern = PlaceholderPattern('{{name}}')
        text = '{{name}} and {{name}} are the same'

        occurrences = pattern.extract_from_text(text)

        assert len(occurrences) == 2
        assert all(occ == '{{name}}' for occ in occurrences)

    def test_extract_from_text_returns_empty_list_when_not_found(self) -> None:
        """Test that extract_from_text returns empty list when pattern not found."""
        pattern = PlaceholderPattern('{{name}}')
        text = 'No placeholders here'

        occurrences = pattern.extract_from_text(text)

        assert occurrences == []

    def test_replace_in_text_replaces_all_occurrences(self) -> None:
        """Test replacing all occurrences of pattern in text."""
        pattern = PlaceholderPattern('{{name}}')
        text = 'Hello {{name}}, welcome {{name}}!'

        result = pattern.replace_in_text(text, 'Alice')

        assert result == 'Hello Alice, welcome Alice!'

    def test_replace_in_text_returns_unchanged_when_not_found(self) -> None:
        """Test that replace_in_text returns unchanged text when pattern not found."""
        pattern = PlaceholderPattern('{{name}}')
        text = 'Hello world!'

        result = pattern.replace_in_text(text, 'Alice')

        assert result == 'Hello world!'


class TestPlaceholderPatternFromName:
    """Tests for PlaceholderPattern.from_name class method."""

    def test_from_name_creates_valid_pattern(self) -> None:
        """Test creating pattern from variable name."""
        pattern = PlaceholderPattern.from_name('my_variable')

        assert pattern.raw == '{{my_variable}}'
        assert pattern.name == 'my_variable'

    def test_from_name_with_underscore_prefix(self) -> None:
        """Test creating pattern from underscore-prefixed name."""
        pattern = PlaceholderPattern.from_name('_private')

        assert pattern.raw == '{{_private}}'
        assert pattern.name == '_private'

    def test_from_name_with_numbers(self) -> None:
        """Test creating pattern from name with numbers."""
        pattern = PlaceholderPattern.from_name('var123')

        assert pattern.raw == '{{var123}}'
        assert pattern.name == 'var123'

    def test_from_name_raises_error_for_empty_name(self) -> None:
        """Test that from_name raises error for empty name."""
        with pytest.raises(InvalidPlaceholderError) as exc_info:
            PlaceholderPattern.from_name('')

        assert 'cannot be empty' in str(exc_info.value)

    def test_from_name_raises_error_for_name_starting_with_digit(self) -> None:
        """Test that from_name raises error for name starting with digit."""
        with pytest.raises(InvalidPlaceholderError) as exc_info:
            PlaceholderPattern.from_name('1variable')

        assert 'cannot start with a digit' in str(exc_info.value)

    def test_from_name_raises_error_for_invalid_characters(self) -> None:
        """Test that from_name raises error for invalid characters."""
        with pytest.raises(InvalidPlaceholderError) as exc_info:
            PlaceholderPattern.from_name('my-variable')

        assert 'Invalid variable name' in str(exc_info.value)

    def test_from_name_raises_error_for_space_in_name(self) -> None:
        """Test that from_name raises error for space in name."""
        with pytest.raises(InvalidPlaceholderError) as exc_info:
            PlaceholderPattern.from_name('my variable')

        assert 'Invalid variable name' in str(exc_info.value)


class TestPlaceholderPatternExtractAll:
    """Tests for PlaceholderPattern.extract_all_from_text class method."""

    def test_extract_all_finds_single_pattern(self) -> None:
        """Test extracting single pattern from text."""
        text = 'Hello {{name}}, welcome!'

        patterns = PlaceholderPattern.extract_all_from_text(text)

        assert len(patterns) == 1
        assert patterns[0].name == 'name'

    def test_extract_all_finds_multiple_patterns(self) -> None:
        """Test extracting multiple patterns from text."""
        text = '{{greeting}} {{name}}, you are {{age}} years old'

        patterns = PlaceholderPattern.extract_all_from_text(text)

        assert len(patterns) == 3
        names = [p.name for p in patterns]
        assert names == ['greeting', 'name', 'age']

    def test_extract_all_finds_duplicate_patterns(self) -> None:
        """Test extracting duplicate patterns from text."""
        text = '{{name}} and {{name}} are the same'

        patterns = PlaceholderPattern.extract_all_from_text(text)

        assert len(patterns) == 2
        assert all(p.name == 'name' for p in patterns)

    def test_extract_all_returns_empty_list_for_no_patterns(self) -> None:
        """Test that extract_all returns empty list when no patterns found."""
        text = 'No placeholders here'

        patterns = PlaceholderPattern.extract_all_from_text(text)

        assert patterns == []

    def test_extract_all_raises_error_for_malformed_pattern(self) -> None:
        """Test that extract_all raises error for malformed patterns."""
        text = 'Hello {{invalid-name}}, welcome!'

        with pytest.raises(InvalidPlaceholderError) as exc_info:
            PlaceholderPattern.extract_all_from_text(text)

        assert 'malformed placeholder pattern' in str(exc_info.value)


class TestPlaceholderPatternIsValid:
    """Tests for PlaceholderPattern.is_valid_pattern class method."""

    def test_is_valid_pattern_returns_true_for_valid_pattern(self) -> None:
        """Test that is_valid_pattern returns True for valid pattern."""
        assert PlaceholderPattern.is_valid_pattern('{{variable}}') is True

    def test_is_valid_pattern_returns_true_for_underscore_prefix(self) -> None:
        """Test that is_valid_pattern returns True for underscore prefix."""
        assert PlaceholderPattern.is_valid_pattern('{{_private}}') is True

    def test_is_valid_pattern_returns_true_for_numbers(self) -> None:
        """Test that is_valid_pattern returns True for numbers in name."""
        assert PlaceholderPattern.is_valid_pattern('{{var123}}') is True

    def test_is_valid_pattern_returns_false_for_invalid_syntax(self) -> None:
        """Test that is_valid_pattern returns False for invalid syntax."""
        assert PlaceholderPattern.is_valid_pattern('{variable}') is False

    def test_is_valid_pattern_returns_false_for_invalid_identifier(self) -> None:
        """Test that is_valid_pattern returns False for invalid identifier."""
        assert PlaceholderPattern.is_valid_pattern('{{invalid-name}}') is False

    def test_is_valid_pattern_returns_false_for_empty_pattern(self) -> None:
        """Test that is_valid_pattern returns False for empty pattern."""
        assert PlaceholderPattern.is_valid_pattern('') is False

    def test_is_valid_pattern_returns_false_for_digit_start(self) -> None:
        """Test that is_valid_pattern returns False for digit start."""
        assert PlaceholderPattern.is_valid_pattern('{{1variable}}') is False


class TestPlaceholderPatternDunderMethods:
    """Tests for PlaceholderPattern special methods."""

    def test_str_returns_raw_pattern(self) -> None:
        """Test that __str__ returns the raw pattern."""
        pattern = PlaceholderPattern('{{variable}}')
        assert str(pattern) == '{{variable}}'

    def test_repr_returns_developer_representation(self) -> None:
        """Test that __repr__ returns developer representation."""
        pattern = PlaceholderPattern('{{variable}}')
        repr_str = repr(pattern)

        assert 'PlaceholderPattern' in repr_str
        assert '{{variable}}' in repr_str

    def test_eq_returns_true_for_same_pattern(self) -> None:
        """Test equality for same pattern."""
        pattern1 = PlaceholderPattern('{{variable}}')
        pattern2 = PlaceholderPattern('{{variable}}')

        assert pattern1 == pattern2

    def test_eq_returns_false_for_different_patterns(self) -> None:
        """Test inequality for different patterns."""
        pattern1 = PlaceholderPattern('{{variable1}}')
        pattern2 = PlaceholderPattern('{{variable2}}')

        assert pattern1 != pattern2

    def test_eq_returns_not_implemented_for_non_placeholder_pattern(self) -> None:
        """Test that equality with non-PlaceholderPattern returns NotImplemented."""
        pattern = PlaceholderPattern('{{variable}}')

        result = pattern.__eq__('not a PlaceholderPattern')
        assert result is NotImplemented

    def test_hash_is_consistent(self) -> None:
        """Test that hash is consistent for same pattern."""
        pattern1 = PlaceholderPattern('{{variable}}')
        pattern2 = PlaceholderPattern('{{variable}}')

        assert hash(pattern1) == hash(pattern2)

    def test_hash_allows_use_in_set(self) -> None:
        """Test that PlaceholderPattern can be used in a set."""
        pattern1 = PlaceholderPattern('{{var1}}')
        pattern2 = PlaceholderPattern('{{var2}}')
        pattern3 = PlaceholderPattern('{{var1}}')  # Same as pattern1

        pattern_set = {pattern1, pattern2, pattern3}
        assert len(pattern_set) == 2  # pattern1 and pattern3 are duplicates
