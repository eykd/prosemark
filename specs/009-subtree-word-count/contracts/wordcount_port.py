"""Contract specification for WordCounterPort.

This file defines the behavioral contract that all WordCounterPort implementations
must satisfy. It serves as executable documentation and will be used to generate
contract tests.
"""

from typing import Protocol


class WordCounterPort(Protocol):
    """Port interface for word counting implementations.

    All implementations must count words according to US English conventions:
    - Split on whitespace
    - Contractions count as one word (don't, it's, can't)
    - Hyphenated compounds count as one word (well-known, state-of-the-art)
    - Numbers count as individual words (123, 3.14, 2025)
    - URLs count as single words (https://example.com)
    - Email addresses count as single words (user@example.com)
    - Em-dashes and en-dashes handled per US English usage patterns
    - Empty strings return 0
    - Whitespace is normalized (multiple spaces/newlines count as single separator)
    """

    def count_words(self, text: str) -> int:
        r"""Count words in text using US English conventions.

        Args:
            text: Input text to analyze. May be empty.

        Returns:
            Number of words found. Always >= 0.

        Examples:
            >>> counter.count_words('Hello world')
            2

            >>> counter.count_words("don't it's can't")
            3

            >>> counter.count_words('well-known state-of-the-art')
            2

            >>> counter.count_words('There are 123 items')
            4

            >>> counter.count_words('Visit https://example.com today')
            3

            >>> counter.count_words('Email user@example.com now')
            3

            >>> counter.count_words('')
            0

            >>> counter.count_words('word  \\n\\n  word')
            2

        Contract Requirements:
            - Pure function: No side effects
            - Deterministic: Same input always produces same output
            - Non-negative: count >= 0 for all inputs
            - Fast: O(n) complexity where n = len(text)
            - Safe: Handles empty strings, whitespace-only strings, unicode

        """
        ...


# Contract Test Scenarios
# These scenarios will be used to generate contract tests in
# tests/contract/wordcount/test_wordcount_port.py

CONTRACT_SCENARIOS = [
    # Basic scenarios
    ('Hello world', 2, 'basic two-word sentence'),
    ('', 0, 'empty string'),
    ('word', 1, 'single word'),
    # Contractions
    ("don't", 1, 'contraction with apostrophe'),
    ("it's can't won't", 3, 'multiple contractions'),
    ("I'm you're they're", 3, 'various contraction forms'),
    # Hyphens
    ('well-known', 1, 'hyphenated compound'),
    ('state-of-the-art', 1, 'multi-hyphen compound'),
    ('twenty-one thirty-two', 2, 'multiple hyphenated numbers'),
    # Numbers
    ('123', 1, 'integer'),
    ('3.14', 1, 'decimal'),
    ('There are 123 items', 4, 'sentence with number'),
    ('2025 was year 2024', 4, 'multiple numbers'),
    # URLs
    ('https://example.com', 1, 'HTTPS URL'),
    ('http://test.org', 1, 'HTTP URL'),
    ('Visit https://example.com today', 3, 'URL in sentence'),
    ('https://example.com and http://test.org', 3, 'multiple URLs'),
    # Email addresses
    ('user@example.com', 1, 'email address'),
    ('Email user@example.com now', 3, 'email in sentence'),
    ('admin@test.org and user@example.com', 3, 'multiple emails'),
    # Whitespace normalization
    ('word  word', 2, 'double space'),
    ('word\nword', 2, 'newline separator'),
    ('word\tword', 2, 'tab separator'),
    ('word  \n\n  word', 2, 'mixed whitespace'),
    ('  word  ', 1, 'leading/trailing whitespace'),
    # Punctuation
    ('Hello, world!', 2, 'comma and exclamation'),
    ('Really?', 1, 'question mark'),
    ('Yes.', 1, 'period'),
    ("'quoted'", 1, 'single quotes'),
    ('"quoted"', 1, 'double quotes'),
    # Em-dashes and en-dashes
    ('word—word', 2, 'em-dash separating words'),
    ('word–word', 2, 'en-dash separating words'),  # noqa: RUF001
    ('word — word', 2, 'spaced em-dash'),
    # Mixed scenarios (from spec acceptance scenarios)
    ('Visit https://example.com or email user@example.com', 5, 'URL and email together'),
    ('The well-known solution uses state-of-the-art technology', 6, 'hyphens in sentence'),
    # Edge cases
    ('!!!', 0, 'punctuation only'),
    ('123.456.789', 1, 'number with multiple dots'),
    ('a b c d e', 5, 'single-letter words'),
]
