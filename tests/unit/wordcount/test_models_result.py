"""Unit tests for WordCountResult model."""

import pytest


def test_wordcount_result_creation() -> None:
    """Test WordCountResult creation with count and content."""
    from prosemark.domain.wordcount.models import WordCountResult

    result = WordCountResult(count=42, content='Hello world from test')

    assert result.count == 42
    assert result.content == 'Hello world from test'


def test_wordcount_result_zero_count() -> None:
    """Test WordCountResult with zero count."""
    from prosemark.domain.wordcount.models import WordCountResult

    result = WordCountResult(count=0, content='')

    assert result.count == 0
    assert result.content == ''


def test_wordcount_result_large_count() -> None:
    """Test WordCountResult with large word count."""
    from prosemark.domain.wordcount.models import WordCountResult

    large_content = ' '.join(['word'] * 100000)
    result = WordCountResult(count=100000, content=large_content)

    assert result.count == 100000
    assert len(result.content) > 0


def test_wordcount_result_empty_content() -> None:
    """Test WordCountResult with empty content but zero count."""
    from prosemark.domain.wordcount.models import WordCountResult

    result = WordCountResult(count=0, content='')

    assert result.count == 0
    assert result.content == ''


def test_wordcount_result_immutability() -> None:
    """Test that WordCountResult is immutable (frozen dataclass)."""
    from prosemark.domain.wordcount.models import WordCountResult

    result = WordCountResult(count=5, content='test content')

    # Attempting to modify should raise FrozenInstanceError
    with pytest.raises(AttributeError):  # dataclasses.FrozenInstanceError
        result.count = 10  # type: ignore[misc]


def test_wordcount_result_equality() -> None:
    """Test WordCountResult equality comparison."""
    from prosemark.domain.wordcount.models import WordCountResult

    result1 = WordCountResult(count=5, content='test')
    result2 = WordCountResult(count=5, content='test')
    result3 = WordCountResult(count=6, content='test')
    result4 = WordCountResult(count=5, content='different')

    assert result1 == result2
    assert result1 != result3
    assert result1 != result4


def test_wordcount_result_with_unicode() -> None:
    """Test WordCountResult with unicode content."""
    from prosemark.domain.wordcount.models import WordCountResult

    unicode_content = 'Hello 世界 مرحبا мир'
    result = WordCountResult(count=5, content=unicode_content)

    assert result.count == 5
    assert result.content == unicode_content
