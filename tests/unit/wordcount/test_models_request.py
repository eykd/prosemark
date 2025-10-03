"""Unit tests for WordCountRequest model."""

import pytest

from prosemark.domain.models import NodeId


def test_wordcount_request_with_node_id() -> None:
    """Test WordCountRequest creation with a specific node ID."""
    from prosemark.domain.wordcount.models import WordCountRequest

    node_id = NodeId('0199a89e-e5f4-7ce2-8b02-dcbbb7de3ae8')
    request = WordCountRequest(node_id=node_id, include_empty=False)

    assert request.node_id == node_id
    assert request.include_empty is False


def test_wordcount_request_with_none() -> None:
    """Test WordCountRequest creation with None (all roots)."""
    from prosemark.domain.wordcount.models import WordCountRequest

    request = WordCountRequest(node_id=None, include_empty=False)

    assert request.node_id is None
    assert request.include_empty is False


def test_wordcount_request_include_empty_true() -> None:
    """Test WordCountRequest with include_empty=True."""
    from prosemark.domain.wordcount.models import WordCountRequest

    request = WordCountRequest(node_id=None, include_empty=True)

    assert request.include_empty is True


def test_wordcount_request_include_empty_default() -> None:
    """Test WordCountRequest include_empty defaults to False."""
    from prosemark.domain.wordcount.models import WordCountRequest

    request = WordCountRequest(node_id=None)

    assert request.include_empty is False


def test_wordcount_request_immutability() -> None:
    """Test that WordCountRequest is immutable (frozen dataclass)."""
    from prosemark.domain.wordcount.models import WordCountRequest

    request = WordCountRequest(node_id=None, include_empty=False)

    # Attempting to modify should raise FrozenInstanceError
    with pytest.raises(AttributeError):  # dataclasses.FrozenInstanceError
        request.include_empty = True  # type: ignore[misc]


def test_wordcount_request_equality() -> None:
    """Test WordCountRequest equality comparison."""
    from prosemark.domain.wordcount.models import WordCountRequest

    node_id = NodeId('0199a89e-e5f4-7ce2-8b02-dcbbb7de3ae8')
    request1 = WordCountRequest(node_id=node_id, include_empty=False)
    request2 = WordCountRequest(node_id=node_id, include_empty=False)
    request3 = WordCountRequest(node_id=node_id, include_empty=True)

    assert request1 == request2
    assert request1 != request3
