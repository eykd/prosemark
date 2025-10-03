"""Use cases for word counting operations."""

from prosemark.app.compile.use_cases import CompileSubtreeUseCase
from prosemark.domain.compile.models import CompileRequest
from prosemark.domain.wordcount.models import WordCountRequest, WordCountResult
from prosemark.domain.wordcount.service import WordCountService


class WordCountUseCase:
    """Use case for counting words in node subtrees.

    Orchestrates compilation (via CompileSubtreeUseCase) and word counting
    (via WordCountService) to provide end-to-end word count functionality.
    """

    def __init__(self, compile_use_case: CompileSubtreeUseCase, word_count_service: WordCountService) -> None:
        """Initialize use case with dependencies.

        Args:
            compile_use_case: Use case for compiling node subtrees
            word_count_service: Service for counting words

        """
        self._compile_use_case = compile_use_case
        self._word_count_service = word_count_service

    def count_words(self, request: WordCountRequest) -> WordCountResult:
        """Count words in a node subtree.

        Args:
            request: Word count request specifying node and options

        Returns:
            Word count result with count and content

        Raises:
            NodeNotFoundError: If specified node doesn't exist
            CompileNodeNotFoundError: If compilation fails due to missing nodes

        """
        # Step 1: Compile the subtree to get text content
        compile_request = CompileRequest(node_id=request.node_id, include_empty=request.include_empty)

        compile_result = self._compile_use_case.compile_subtree(compile_request)

        # Step 2: Count words in the compiled content
        return self._word_count_service.count_text(compile_result.content)
