"""Contract tests for CompileRequest with optional node_id field.

These tests verify that CompileRequest accepts both NodeId and None for its node_id field,
supporting both single-node and multi-root compilation modes.
"""

import pytest

from prosemark.domain.compile.models import CompileRequest
from prosemark.domain.models import NodeId


def test_compile_request_accepts_node_id() -> None:
    """CompileRequest accepts NodeId for node_id."""
    node_id = NodeId.generate()
    request = CompileRequest(node_id=node_id, include_empty=False)
    assert request.node_id == node_id


def test_compile_request_accepts_none() -> None:
    """CompileRequest accepts None for node_id."""
    request = CompileRequest(node_id=None, include_empty=False)
    assert request.node_id is None


def test_compile_request_is_frozen() -> None:
    """CompileRequest is immutable (frozen dataclass)."""
    request = CompileRequest(node_id=None, include_empty=False)
    with pytest.raises(AttributeError):  # Frozen dataclass raises AttributeError
        request.node_id = NodeId.generate()  # type: ignore[misc]


def test_compile_request_with_include_empty_and_none_node_id() -> None:
    """CompileRequest supports both None node_id and include_empty flag."""
    request = CompileRequest(node_id=None, include_empty=True)
    assert request.node_id is None
    assert request.include_empty is True


def test_compile_request_default_include_empty() -> None:
    """CompileRequest defaults include_empty to False."""
    request = CompileRequest(node_id=None)
    assert request.include_empty is False


def test_compile_request_with_specific_node_and_include_empty() -> None:
    """CompileRequest supports specific NodeId with include_empty flag."""
    node_id = NodeId.generate()
    request = CompileRequest(node_id=node_id, include_empty=True)
    assert request.node_id == node_id
    assert request.include_empty is True
