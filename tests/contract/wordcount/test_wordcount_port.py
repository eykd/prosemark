"""Contract tests for WordCounterPort implementations.

These tests verify that any implementation of WordCounterPort satisfies
the behavioral contract defined in the port specification.
"""

import sys
from pathlib import Path

import pytest

# Add specs/contracts to path to import CONTRACT_SCENARIOS
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent / 'specs' / '009-subtree-word-count' / 'contracts'))

from wordcount_port import CONTRACT_SCENARIOS  # type: ignore[import-not-found]


@pytest.mark.parametrize(('text', 'expected_count', 'description'), CONTRACT_SCENARIOS)
def test_wordcounter_contract(text: str, expected_count: int, description: str) -> None:
    """Test WordCounterPort implementation against contract scenarios.

    This test will FAIL until StandardWordCounter is implemented.
    """
    # Import the implementation to test
    # This will fail initially - that's expected for TDD
    from prosemark.adapters.wordcount.counter_standard import StandardWordCounter

    counter = StandardWordCounter()
    actual_count = counter.count_words(text)

    assert actual_count == expected_count, (
        f'Failed scenario: {description}\nText: {text!r}\nExpected: {expected_count} words\nGot: {actual_count} words'
    )


def test_wordcounter_port_protocol_compliance() -> None:
    """Test that StandardWordCounter implements WordCounterPort protocol."""
    from prosemark.adapters.wordcount.counter_standard import StandardWordCounter

    counter = StandardWordCounter()

    # Verify protocol compliance
    assert hasattr(counter, 'count_words'), 'StandardWordCounter must have count_words method'
    assert callable(counter.count_words), 'count_words must be callable'

    # Type checking happens at static analysis time, but we can verify runtime behavior
    assert isinstance(counter.count_words('test'), int), 'count_words must return int'


def test_wordcounter_returns_non_negative() -> None:
    """Test that count_words always returns non-negative integers."""
    from prosemark.adapters.wordcount.counter_standard import StandardWordCounter

    counter = StandardWordCounter()

    # Test various inputs that should all return >= 0
    test_inputs = ['', '   ', '\n\n', '!!!', 'word', 'multiple words', '-5']
    for text in test_inputs:
        count = counter.count_words(text)
        assert count >= 0, f'count_words({text!r}) returned negative: {count}'
