"""Helper functions for batch materialization test assertions."""
# ruff: noqa: S101

import re
from pathlib import Path
from typing import TypedDict


class BatchResult(TypedDict):
    """Type definition for batch materialization result."""

    type: str
    total_placeholders: int
    successful_materializations: int
    failed_materializations: int
    execution_time: float
    message: str


class FailureDetail(TypedDict):
    """Type definition for failure detail."""

    placeholder_title: str
    error_type: str
    error_message: str


class PartialFailureResult(BatchResult):
    """Type definition for partial failure result."""

    successes: list[str]
    failures: list[FailureDetail]


def assert_batch_result_valid(result: BatchResult) -> None:
    """Assert that a batch materialization result has valid structure."""
    assert 'type' in result
    assert result['type'] == 'batch'
    assert 'total_placeholders' in result
    assert 'successful_materializations' in result
    assert 'failed_materializations' in result
    assert 'execution_time' in result
    assert 'message' in result

    # Validate counts match
    total = result['total_placeholders']
    successes = result['successful_materializations']
    failures = result['failed_materializations']
    assert total == successes + failures, f'Total {total} != successes {successes} + failures {failures}'

    # Validate execution time is reasonable
    assert result['execution_time'] >= 0
    assert result['execution_time'] < 300  # Should complete within 5 minutes


def assert_partial_failure_valid(result: PartialFailureResult) -> None:
    """Assert that a partial failure result has valid structure."""
    assert 'type' in result
    assert result['type'] == 'batch_partial'
    assert 'total_placeholders' in result
    assert 'successful_materializations' in result
    assert 'failed_materializations' in result
    assert 'execution_time' in result
    assert 'message' in result
    assert 'successes' in result
    assert 'failures' in result

    # Validate at least one failure
    assert result['failed_materializations'] > 0
    assert len(result['failures']) == result['failed_materializations']

    # Validate failure structure
    for failure in result['failures']:
        assert 'placeholder_title' in failure
        assert 'error_type' in failure
        assert 'error_message' in failure
        assert failure['error_type'] in {
            'filesystem',
            'validation',
            'already_materialized',
            'binder_integrity',
            'id_generation',
        }


def assert_all_placeholders_materialized(project_dir: Path) -> None:
    """Assert that all placeholders in the binder have been materialized."""
    binder_path = project_dir / '_binder.md'
    assert binder_path.exists(), f'Binder not found at {binder_path}'

    content = binder_path.read_text()

    # Find all links in the managed block
    managed_block_pattern = r'<!-- BEGIN_MANAGED_BLOCK -->(.*?)<!-- END_MANAGED_BLOCK -->'
    managed_match = re.search(managed_block_pattern, content, re.DOTALL)
    assert managed_match, 'No managed block found in binder'

    managed_content = managed_match.group(1)

    # Find all links - they should all have hrefs now
    link_pattern = r'\[([^\]]+)\]\(([^)]*)\)'
    links = re.findall(link_pattern, managed_content)

    for title, href in links:
        assert href, f"Placeholder '{title}' was not materialized (empty href)"
        assert href.endswith('.md'), f"Invalid href for '{title}': {href}"

        # Verify the file exists
        node_file = project_dir / href
        assert node_file.exists(), f'Node file not found: {node_file}'

        # Verify the notes file exists
        node_id = href[:-3]  # Remove .md extension
        notes_file = project_dir / f'{node_id}.notes.md'
        assert notes_file.exists(), f'Notes file not found: {notes_file}'


def count_placeholders_in_binder(project_dir: Path) -> int:
    """Count the number of placeholders (empty links) in the binder."""
    binder_path = project_dir / '_binder.md'
    if not binder_path.exists():
        return 0

    content = binder_path.read_text()

    # Find managed block
    managed_block_pattern = r'<!-- BEGIN_MANAGED_BLOCK -->(.*?)<!-- END_MANAGED_BLOCK -->'
    managed_match = re.search(managed_block_pattern, content, re.DOTALL)
    if not managed_match:
        return 0

    managed_content = managed_match.group(1)

    # Count empty links (placeholders)
    link_pattern = r'\[([^\]]+)\]\(([^)]*)\)'
    links = re.findall(link_pattern, managed_content)

    return sum(1 for _, href in links if not href)


def count_materialized_nodes_in_binder(project_dir: Path) -> int:
    """Count the number of materialized nodes (non-empty links) in the binder."""
    binder_path = project_dir / '_binder.md'
    if not binder_path.exists():
        return 0

    content = binder_path.read_text()

    # Find managed block
    managed_block_pattern = r'<!-- BEGIN_MANAGED_BLOCK -->(.*?)<!-- END_MANAGED_BLOCK -->'
    managed_match = re.search(managed_block_pattern, content, re.DOTALL)
    if not managed_match:
        return 0

    managed_content = managed_match.group(1)

    # Count non-empty links (materialized nodes)
    link_pattern = r'\[([^\]]+)\]\(([^)]*)\)'
    links = re.findall(link_pattern, managed_content)

    return sum(1 for _, href in links if href)


def assert_node_files_created(project_dir: Path, node_id: str, title: str | None = None) -> None:
    """Assert that node files were created correctly."""
    # Check main node file
    node_file = project_dir / f'{node_id}.md'
    assert node_file.exists(), f'Node file not found: {node_file}'

    # Check notes file
    notes_file = project_dir / f'{node_id}.notes.md'
    assert notes_file.exists(), f'Notes file not found: {notes_file}'

    # Validate content if title provided
    if title:
        node_content = node_file.read_text()
        assert title in node_content or f'# {title}' in node_content, f"Title '{title}' not found in node file"


def assert_valid_uuidv7(node_id: str) -> None:
    """Assert that a node ID is a valid UUIDv7."""
    # UUIDv7 pattern: 8-4-4-4-12 hex characters
    uuid_pattern = r'^[0-9a-f]{8}-[0-9a-f]{4}-7[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$'
    assert re.match(uuid_pattern, node_id, re.IGNORECASE), f'Invalid UUIDv7: {node_id}'


def extract_node_ids_from_binder(project_dir: Path) -> list[str]:
    """Extract all node IDs from the binder file."""
    binder_path = project_dir / '_binder.md'
    if not binder_path.exists():
        return []

    content = binder_path.read_text()

    # Find all node IDs in links (format: [title](node-id.md))
    node_id_pattern = r'\[([^\]]+)\]\(([0-9a-f-]{36})\.md\)'
    matches = re.findall(node_id_pattern, content, re.IGNORECASE)

    return [node_id for _, node_id in matches]


def assert_progress_reported(captured_output: str, expected_count: int) -> None:
    """Assert that progress was reported during batch materialization."""
    # Check for progress indicators
    progress_patterns = [
        r'Found \d+ placeholder[s]? to materialize',
        r"✓ Materialized '[^']+' →",
        r'Successfully materialized (all )?\d+ placeholder[s]?',
        r'Materialized \d+ of \d+ placeholder[s]?',
    ]

    for pattern in progress_patterns:
        assert re.search(pattern, captured_output), f'Progress pattern not found: {pattern}'

    # Count successful materializations reported
    success_pattern = r"✓ Materialized '[^']+' → [0-9a-f-]{36}"
    success_matches = re.findall(success_pattern, captured_output)
    # Allow for partial matches in case of failures
    assert len(success_matches) <= expected_count, (
        f'Too many successes reported: {len(success_matches)} > {expected_count}'
    )
