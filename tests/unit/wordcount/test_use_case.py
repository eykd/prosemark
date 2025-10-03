"""Unit tests for WordCountUseCase."""

from unittest.mock import Mock

import pytest

from prosemark.domain.compile.models import CompileResult
from prosemark.domain.models import NodeId
from prosemark.exceptions import NodeNotFoundError


def test_wordcount_usecase_dependency_injection() -> None:
    """Test WordCountUseCase accepts required dependencies."""
    from prosemark.app.wordcount.use_cases import WordCountUseCase

    mock_compile = Mock()
    mock_service = Mock()

    use_case = WordCountUseCase(compile_use_case=mock_compile, word_count_service=mock_service)

    assert use_case._compile_use_case is mock_compile
    assert use_case._word_count_service is mock_service


def test_wordcount_usecase_with_node_id() -> None:
    """Test count_words() with specific node ID."""
    from prosemark.app.wordcount.use_cases import WordCountUseCase
    from prosemark.domain.wordcount.models import WordCountRequest, WordCountResult

    mock_compile = Mock()
    mock_compile.compile_subtree.return_value = CompileResult(
        content='hello world test', node_count=1, total_nodes=1, skipped_empty=0
    )

    mock_service = Mock()
    mock_service.count_text.return_value = WordCountResult(count=3, content='hello world test')

    use_case = WordCountUseCase(compile_use_case=mock_compile, word_count_service=mock_service)

    node_id = NodeId('0199a89e-e5f4-7ce2-8b02-dcbbb7de3ae8')
    request = WordCountRequest(node_id=node_id, include_empty=False)
    result = use_case.count_words(request)

    # Verify compile was called with correct request
    assert mock_compile.compile_subtree.called
    compile_request = mock_compile.compile_subtree.call_args[0][0]
    assert compile_request.node_id == node_id
    assert compile_request.include_empty is False

    # Verify service was called with compiled content
    mock_service.count_text.assert_called_once_with('hello world test')

    assert result.count == 3


def test_wordcount_usecase_without_node_id() -> None:
    """Test count_words() without node ID (all roots)."""
    from prosemark.app.wordcount.use_cases import WordCountUseCase
    from prosemark.domain.wordcount.models import WordCountRequest, WordCountResult

    mock_compile = Mock()
    mock_compile.compile_subtree.return_value = CompileResult(
        content='all roots content', node_count=1, total_nodes=1, skipped_empty=0
    )

    mock_service = Mock()
    mock_service.count_text.return_value = WordCountResult(count=3, content='all roots content')

    use_case = WordCountUseCase(compile_use_case=mock_compile, word_count_service=mock_service)

    request = WordCountRequest(node_id=None, include_empty=False)
    result = use_case.count_words(request)

    # Verify compile was called with None node_id
    compile_request = mock_compile.compile_subtree.call_args[0][0]
    assert compile_request.node_id is None

    assert result.count == 3


def test_wordcount_usecase_include_empty_parameter() -> None:
    """Test include_empty parameter is passed to compile request."""
    from prosemark.app.wordcount.use_cases import WordCountUseCase
    from prosemark.domain.wordcount.models import WordCountRequest, WordCountResult

    mock_compile = Mock()
    mock_compile.compile_subtree.return_value = CompileResult(
        content='content', node_count=1, total_nodes=1, skipped_empty=0
    )

    mock_service = Mock()
    mock_service.count_text.return_value = WordCountResult(count=1, content='content')

    use_case = WordCountUseCase(compile_use_case=mock_compile, word_count_service=mock_service)

    request = WordCountRequest(node_id=None, include_empty=True)
    use_case.count_words(request)

    # Verify include_empty was passed through
    compile_request = mock_compile.compile_subtree.call_args[0][0]
    assert compile_request.include_empty is True


def test_wordcount_usecase_error_propagation_node_not_found() -> None:
    """Test NodeNotFoundError propagates from compile layer."""
    from prosemark.app.wordcount.use_cases import WordCountUseCase
    from prosemark.domain.wordcount.models import WordCountRequest

    mock_compile = Mock()
    mock_compile.compile_subtree.side_effect = NodeNotFoundError('Node not found')

    mock_service = Mock()

    use_case = WordCountUseCase(compile_use_case=mock_compile, word_count_service=mock_service)

    node_id = NodeId('0199a89e-e5f4-7ce2-8b02-dcbbb7de3ae8')
    request = WordCountRequest(node_id=node_id)

    with pytest.raises(NodeNotFoundError):
        use_case.count_words(request)


def test_wordcount_usecase_result_construction() -> None:
    """Test use case returns result from service."""
    from prosemark.app.wordcount.use_cases import WordCountUseCase
    from prosemark.domain.wordcount.models import WordCountRequest, WordCountResult

    mock_compile = Mock()
    mock_compile.compile_subtree.return_value = CompileResult(
        content='test content here', node_count=1, total_nodes=1, skipped_empty=0
    )

    expected_result = WordCountResult(count=3, content='test content here')
    mock_service = Mock()
    mock_service.count_text.return_value = expected_result

    use_case = WordCountUseCase(compile_use_case=mock_compile, word_count_service=mock_service)

    request = WordCountRequest(node_id=None)
    result = use_case.count_words(request)

    assert result is expected_result
    assert result.count == 3
    assert result.content == 'test content here'


def test_wordcount_usecase_empty_content() -> None:
    """Test use case handles empty compiled content."""
    from prosemark.app.wordcount.use_cases import WordCountUseCase
    from prosemark.domain.wordcount.models import WordCountRequest, WordCountResult

    mock_compile = Mock()
    mock_compile.compile_subtree.return_value = CompileResult(content='', node_count=0, total_nodes=1, skipped_empty=1)

    mock_service = Mock()
    mock_service.count_text.return_value = WordCountResult(count=0, content='')

    use_case = WordCountUseCase(compile_use_case=mock_compile, word_count_service=mock_service)

    request = WordCountRequest(node_id=None)
    result = use_case.count_words(request)

    assert result.count == 0
    assert result.content == ''
