"""Unit tests for WordCountService."""

from unittest.mock import Mock


def test_wordcount_service_dependency_injection() -> None:
    """Test WordCountService accepts WordCounterPort dependency."""
    from prosemark.domain.wordcount.service import WordCountService

    mock_counter = Mock()
    mock_counter.count_words.return_value = 10

    service = WordCountService(counter=mock_counter)

    assert service._counter is mock_counter


def test_wordcount_service_count_text_delegates_to_counter() -> None:
    """Test count_text() delegates word counting to injected counter."""
    from prosemark.domain.wordcount.service import WordCountService

    mock_counter = Mock()
    mock_counter.count_words.return_value = 42

    service = WordCountService(counter=mock_counter)
    result = service.count_text('test content')

    # Verify counter was called with the text
    mock_counter.count_words.assert_called_once_with('test content')
    assert result.count == 42


def test_wordcount_service_result_construction() -> None:
    """Test count_text() constructs WordCountResult with count and content."""
    from prosemark.domain.wordcount.service import WordCountService

    mock_counter = Mock()
    mock_counter.count_words.return_value = 5

    service = WordCountService(counter=mock_counter)
    result = service.count_text('hello world test')

    assert result.count == 5
    assert result.content == 'hello world test'


def test_wordcount_service_with_empty_text() -> None:
    """Test count_text() with empty string."""
    from prosemark.domain.wordcount.service import WordCountService

    mock_counter = Mock()
    mock_counter.count_words.return_value = 0

    service = WordCountService(counter=mock_counter)
    result = service.count_text('')

    assert result.count == 0
    assert result.content == ''


def test_wordcount_service_with_large_text() -> None:
    """Test count_text() with large text content."""
    from prosemark.domain.wordcount.service import WordCountService

    mock_counter = Mock()
    mock_counter.count_words.return_value = 10000

    service = WordCountService(counter=mock_counter)
    large_text = ' '.join(['word'] * 10000)
    result = service.count_text(large_text)

    assert result.count == 10000
    assert result.content == large_text


def test_wordcount_service_preserves_content() -> None:
    """Test that service preserves original content in result."""
    from prosemark.domain.wordcount.service import WordCountService

    mock_counter = Mock()
    mock_counter.count_words.return_value = 3

    service = WordCountService(counter=mock_counter)
    original_text = 'unchanged content here'
    result = service.count_text(original_text)

    # Content should be exactly as provided (for debugging/testing)
    assert result.content == original_text
