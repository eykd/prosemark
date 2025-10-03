"""Port interface for word counting."""

from typing import Protocol  # pragma: no cover


class WordCounterPort(Protocol):  # pragma: no cover
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

    Examples:
        >>> counter.count_words('Hello world')
        2
        >>> counter.count_words("don't it's")
        2
        >>> counter.count_words('well-known')
        1
        >>> counter.count_words('There are 123 items')
        4
        >>> counter.count_words('https://example.com')
        1
        >>> counter.count_words('')
        0

    """

    def count_words(self, text: str) -> int:  # pragma: no cover
        """Count words in text using US English conventions.

        Args:
            text: Input text to analyze. May be empty.

        Returns:
            Number of words found. Always >= 0.

        Contract Requirements:
            - Pure function: No side effects
            - Deterministic: Same input always produces same output
            - Non-negative: count >= 0 for all inputs
            - Fast: O(n) complexity where n = len(text)
            - Safe: Handles empty strings, whitespace-only strings, unicode

        """
        ...  # pragma: no cover
