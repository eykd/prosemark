"""Test fixtures for binders with placeholders for materialize all command."""

import tempfile
from collections.abc import Iterator
from pathlib import Path

import pytest


@pytest.fixture
def binder_with_placeholders() -> Iterator[Path]:
    """Create a test binder with multiple placeholders."""
    with tempfile.TemporaryDirectory() as tmpdir:
        binder_path = Path(tmpdir) / '_binder.md'
        binder_content = """# Test Project

<!-- BEGIN_MANAGED_BLOCK -->
- [Chapter 1]()
  - [Section 1.1]()
  - [Section 1.2]()
    - [Subsection 1.2.1]()
- [Chapter 2]()
- [Chapter 3]()
  - [Section 3.1]()
- [Appendix A]()
<!-- END_MANAGED_BLOCK -->
"""
        binder_path.write_text(binder_content)
        yield Path(tmpdir)


@pytest.fixture
def binder_with_no_placeholders() -> Iterator[Path]:
    """Create a test binder with all nodes already materialized."""
    with tempfile.TemporaryDirectory() as tmpdir:
        binder_path = Path(tmpdir) / '_binder.md'
        binder_content = """# Test Project

<!-- BEGIN_MANAGED_BLOCK -->
- [Chapter 1](01923f0c-1234-7123-8abc-def012345678.md)
  - [Section 1.1](01923f0c-1234-7123-8abc-def012345679.md)
- [Chapter 2](01923f0c-1234-7123-8abc-def012345680.md)
<!-- END_MANAGED_BLOCK -->
"""
        binder_path.write_text(binder_content)

        # Create the corresponding node files
        for node_id in [
            '01923f0c-1234-7123-8abc-def012345678',
            '01923f0c-1234-7123-8abc-def012345679',
            '01923f0c-1234-7123-8abc-def012345680',
        ]:
            node_file = Path(tmpdir) / f'{node_id}.md'
            node_file.write_text(f'# Node {node_id}\n\nContent here.')
            notes_file = Path(tmpdir) / f'{node_id}.notes.md'
            notes_file.write_text(f'# Notes for {node_id}\n')

        yield Path(tmpdir)


@pytest.fixture
def binder_with_mixed_nodes() -> Iterator[Path]:
    """Create a test binder with some materialized and some placeholder nodes."""
    with tempfile.TemporaryDirectory() as tmpdir:
        binder_path = Path(tmpdir) / '_binder.md'
        binder_content = """# Test Project

<!-- BEGIN_MANAGED_BLOCK -->
- [Chapter 1](01923f0c-1234-7123-8abc-def012345678.md)
  - [Section 1.1]()
  - [Section 1.2]()
- [Chapter 2]()
- [Chapter 3](01923f0c-1234-7123-8abc-def012345679.md)
  - [Section 3.1]()
- [Appendix A]()
<!-- END_MANAGED_BLOCK -->
"""
        binder_path.write_text(binder_content)

        # Create the materialized node files
        for node_id, title in [
            ('01923f0c-1234-7123-8abc-def012345678', 'Chapter 1'),
            ('01923f0c-1234-7123-8abc-def012345679', 'Chapter 3'),
        ]:
            node_file = Path(tmpdir) / f'{node_id}.md'
            node_file.write_text(f'# {title}\n\nContent here.')
            notes_file = Path(tmpdir) / f'{node_id}.notes.md'
            notes_file.write_text(f'# Notes for {title}\n')

        yield Path(tmpdir)


@pytest.fixture
def binder_with_large_number_of_placeholders() -> Iterator[Path]:
    """Create a test binder with 100+ placeholders for performance testing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        binder_path = Path(tmpdir) / '_binder.md'

        # Start building binder content
        lines = ['# Large Test Project', '', '<!-- BEGIN_MANAGED_BLOCK -->']

        # Create 100 placeholders in a hierarchical structure
        for i in range(1, 21):  # 20 chapters
            lines.append(f'- [Chapter {i}]()')
            # 5 sections per chapter = 100 total sections
            lines.extend(f'  - [Section {i}.{j}]()' for j in range(1, 6))

        lines.append('<!-- END_MANAGED_BLOCK -->')

        binder_content = '\n'.join(lines)
        binder_path.write_text(binder_content)

        yield Path(tmpdir)


@pytest.fixture
def binder_with_invalid_placeholder_names() -> Iterator[Path]:
    """Create a test binder with placeholders containing invalid characters."""
    with tempfile.TemporaryDirectory() as tmpdir:
        binder_path = Path(tmpdir) / '_binder.md'
        binder_content = """# Test Project

<!-- BEGIN_MANAGED_BLOCK -->
- [Valid Chapter]()
- [Chapter with / slash]()
- [Chapter with \\ backslash]()
- [Chapter: with colon]()
- [Chapter with | pipe]()
<!-- END_MANAGED_BLOCK -->
"""
        binder_path.write_text(binder_content)
        yield Path(tmpdir)


@pytest.fixture
def empty_binder() -> Iterator[Path]:
    """Create an empty binder file."""
    with tempfile.TemporaryDirectory() as tmpdir:
        binder_path = Path(tmpdir) / '_binder.md'
        binder_content = """# Empty Project

<!-- BEGIN_MANAGED_BLOCK -->
<!-- END_MANAGED_BLOCK -->
"""
        binder_path.write_text(binder_content)
        yield Path(tmpdir)


@pytest.fixture
def no_binder() -> Iterator[Path]:
    """Create a directory without a binder file."""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create some other files but no _binder.md
        readme_path = Path(tmpdir) / 'README.md'
        readme_path.write_text('# Project without binder\n')
        yield Path(tmpdir)
