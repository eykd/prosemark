"""Standard word counter implementation using regex tokenization."""

import re


class StandardWordCounter:
    """Regex-based word counter implementing US English conventions.

    Uses pattern matching to:
    - Preserve URLs as single tokens
    - Preserve email addresses as single tokens
    - Preserve contractions (apostrophes within words)
    - Preserve hyphenated compounds
    - Count numbers as words
    - Normalize whitespace
    - Strip punctuation from word boundaries
    """

    # Compiled regex patterns for efficiency
    _URL_PATTERN = re.compile(r'https?://\S+')
    _EMAIL_PATTERN = re.compile(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b')
    # Match hyphenated compounds first (must have at least one hyphen), then contractions, then numbers, then regular words
    # Use \w for Unicode word character support
    _WORD_PATTERN = re.compile(r"\w+(?:-\w+)+|\w+['']\w+|[0-9]+(?:\.[0-9]+)*|\w+", re.UNICODE)

    def count_words(self, text: str) -> int:
        """Count words in text using US English conventions.

        Args:
            text: Input text to analyze

        Returns:
            Number of words found (>= 0)

        Algorithm:
            1. Extract and preserve URLs as single tokens
            2. Extract and preserve emails as single tokens
            3. Replace preserved tokens with placeholders
            4. Replace em-dashes and en-dashes with spaces (they separate words)
            5. Tokenize remaining text using word pattern
            6. Count all tokens

        """
        if not text or not text.strip():
            return 0

        # Step 1: Find and preserve URLs
        urls = self._URL_PATTERN.findall(text)
        url_count = len(urls)

        # Replace URLs with space to avoid interfering with other patterns
        text = self._URL_PATTERN.sub(' ', text)

        # Step 2: Find and preserve emails
        emails = self._EMAIL_PATTERN.findall(text)
        email_count = len(emails)

        # Replace emails with space
        text = self._EMAIL_PATTERN.sub(' ', text)

        # Step 3: Replace em-dashes (U+2014) and en-dashes (U+2013) with spaces
        # These are word separators, unlike hyphens which join compounds
        text = text.replace('—', ' ')  # em-dash
        text = text.replace('\u2013', ' ')  # en-dash

        # Step 4: Tokenize remaining text
        words = self._WORD_PATTERN.findall(text)

        # Count all remaining words
        word_count = len(words)

        # Total = regular words + URLs + emails
        return word_count + url_count + email_count
