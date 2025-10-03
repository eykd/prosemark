"""Unit tests for StandardWordCounter implementation."""


def test_standard_counter_basic_words() -> None:
    """Test counting basic space-separated words."""
    from prosemark.adapters.wordcount.counter_standard import StandardWordCounter

    counter = StandardWordCounter()

    assert counter.count_words('hello') == 1
    assert counter.count_words('hello world') == 2
    assert counter.count_words('one two three') == 3


def test_standard_counter_empty_string() -> None:
    """Test counting empty string returns 0."""
    from prosemark.adapters.wordcount.counter_standard import StandardWordCounter

    counter = StandardWordCounter()

    assert counter.count_words('') == 0


def test_standard_counter_whitespace_only() -> None:
    """Test counting whitespace-only string returns 0."""
    from prosemark.adapters.wordcount.counter_standard import StandardWordCounter

    counter = StandardWordCounter()

    assert counter.count_words('   ') == 0
    assert counter.count_words('\n\n') == 0
    assert counter.count_words('\t\t') == 0


def test_standard_counter_contractions() -> None:
    """Test contractions count as single words."""
    from prosemark.adapters.wordcount.counter_standard import StandardWordCounter

    counter = StandardWordCounter()

    assert counter.count_words("don't") == 1
    assert counter.count_words("it's") == 1
    assert counter.count_words("won't can't") == 2


def test_standard_counter_hyphens() -> None:
    """Test hyphenated compounds count as single words."""
    from prosemark.adapters.wordcount.counter_standard import StandardWordCounter

    counter = StandardWordCounter()

    assert counter.count_words('well-known') == 1
    assert counter.count_words('state-of-the-art') == 1
    assert counter.count_words('twenty-one thirty-two') == 2


def test_standard_counter_numbers() -> None:
    """Test numbers count as words."""
    from prosemark.adapters.wordcount.counter_standard import StandardWordCounter

    counter = StandardWordCounter()

    assert counter.count_words('123') == 1
    assert counter.count_words('3.14') == 1
    assert counter.count_words('There are 123 items') == 4


def test_standard_counter_urls() -> None:
    """Test URLs count as single words."""
    from prosemark.adapters.wordcount.counter_standard import StandardWordCounter

    counter = StandardWordCounter()

    assert counter.count_words('https://example.com') == 1
    assert counter.count_words('http://test.org') == 1
    assert counter.count_words('Visit https://example.com today') == 3


def test_standard_counter_emails() -> None:
    """Test email addresses count as single words."""
    from prosemark.adapters.wordcount.counter_standard import StandardWordCounter

    counter = StandardWordCounter()

    assert counter.count_words('user@example.com') == 1
    assert counter.count_words('Email user@example.com now') == 3


def test_standard_counter_whitespace_normalization() -> None:
    """Test multiple spaces/newlines normalized to single separator."""
    from prosemark.adapters.wordcount.counter_standard import StandardWordCounter

    counter = StandardWordCounter()

    assert counter.count_words('word  word') == 2
    assert counter.count_words('word\nword') == 2
    assert counter.count_words('word\tword') == 2
    assert counter.count_words('word  \n\n  word') == 2


def test_standard_counter_punctuation() -> None:
    """Test punctuation is stripped from word boundaries."""
    from prosemark.adapters.wordcount.counter_standard import StandardWordCounter

    counter = StandardWordCounter()

    assert counter.count_words('Hello, world!') == 2
    assert counter.count_words('Really?') == 1
    assert counter.count_words('Yes.') == 1


def test_standard_counter_leading_trailing_whitespace() -> None:
    """Test leading/trailing whitespace is ignored."""
    from prosemark.adapters.wordcount.counter_standard import StandardWordCounter

    counter = StandardWordCounter()

    assert counter.count_words('  word  ') == 1
    assert counter.count_words('\n\ntest\n\n') == 1


def test_standard_counter_em_dashes() -> None:
    """Test em-dashes separate words."""
    from prosemark.adapters.wordcount.counter_standard import StandardWordCounter

    counter = StandardWordCounter()

    assert counter.count_words('word—word') == 2
    assert counter.count_words('word — word') == 2


def test_standard_counter_en_dashes() -> None:
    """Test en-dashes separate words."""
    from prosemark.adapters.wordcount.counter_standard import StandardWordCounter

    counter = StandardWordCounter()

    assert counter.count_words('word\u2013word') == 2  # en-dash (U+2013)


def test_standard_counter_punctuation_only() -> None:
    """Test punctuation-only strings return 0."""
    from prosemark.adapters.wordcount.counter_standard import StandardWordCounter

    counter = StandardWordCounter()

    assert counter.count_words('!!!') == 0
    assert counter.count_words('???') == 0
    assert counter.count_words('.,;:') == 0


def test_standard_counter_unicode() -> None:
    """Test handling of unicode characters."""
    from prosemark.adapters.wordcount.counter_standard import StandardWordCounter

    counter = StandardWordCounter()

    # Simple unicode test - should count words regardless of script
    result = counter.count_words('Hello 世界')
    assert result >= 2  # At least 2 words (exact count depends on regex)


def test_standard_counter_mixed_scenario() -> None:
    """Test complex mixed scenario from spec."""
    from prosemark.adapters.wordcount.counter_standard import StandardWordCounter

    counter = StandardWordCounter()

    # From spec: "Visit https://example.com or email user@example.com"
    # Expected: 5 words (Visit, https://example.com, or, email, user@example.com)
    assert counter.count_words('Visit https://example.com or email user@example.com') == 5
