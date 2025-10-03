"""Domain service for word counting operations."""

from prosemark.domain.wordcount.models import WordCountResult
from prosemark.ports.wordcount.counter import WordCounterPort


class WordCountService:
    """Domain service that orchestrates word counting.

    This service delegates the actual word counting to an injected
    WordCounterPort implementation, following hexagonal architecture.
    """

    def __init__(self, counter: WordCounterPort) -> None:
        """Initialize service with word counter dependency.

        Args:
            counter: Word counting implementation

        """
        self._counter = counter

    def count_text(self, text: str) -> WordCountResult:
        """Count words in text.

        Args:
            text: Compiled content to count words in

        Returns:
            WordCountResult with count and original content

        """
        count = self._counter.count_words(text)
        return WordCountResult(count=count, content=text)
