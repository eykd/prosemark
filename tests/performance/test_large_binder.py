"""Performance tests for large binder parsing operations."""

import time
from pathlib import Path

import pytest
from typer.testing import CliRunner

from prosemark.adapters.markdown_binder_parser import MarkdownBinderParser
from prosemark.cli.main import app
from prosemark.domain.models import Binder, BinderItem, NodeId


class TestLargeBinderPerformance:
    """Test performance with large binder structures."""

    @pytest.fixture
    def parser(self) -> MarkdownBinderParser:
        """Create a markdown binder parser."""
        return MarkdownBinderParser()

    @pytest.fixture
    def large_flat_structure(self) -> str:
        """Create a large flat binder structure."""
        # 1000 chapters at root level (placeholder entries without node IDs)
        items = [f'- [Chapter {i:04d}]()' for i in range(1000)]
        return '\n'.join(items)

    @pytest.fixture
    def large_nested_structure(self) -> str:
        """Create a large nested binder structure."""
        # 10 parts, each with 20 chapters, each with 5 sections (placeholder entries)
        lines = []
        for part in range(10):
            lines.append(f'- [Part {part:02d}]()')
            for chapter in range(20):
                lines.append(f'  - [Chapter {part}.{chapter:02d}]()')
                lines.extend(f'    - [Section {part}.{chapter}.{section}]()' for section in range(5))
        return '\n'.join(lines)

    def test_parse_large_flat_structure_performance(
        self, parser: MarkdownBinderParser, large_flat_structure: str
    ) -> None:
        """Test parsing performance with large flat structure."""
        # Should parse 1000 items in under 1 second
        start_time = time.time()
        binder = parser.parse_to_binder(large_flat_structure)
        items = binder.roots
        end_time = time.time()

        elapsed = end_time - start_time
        assert elapsed < 1.0, f'Parsing took {elapsed:.3f}s, expected < 1.0s'
        assert len(items) == 1000

        # Verify structure is correct
        assert items[0].display_title == 'Chapter 0000'
        assert items[999].display_title == 'Chapter 0999'
        # These are placeholder entries without node IDs
        assert items[0].node_id is None
        assert items[999].node_id is None

    def test_parse_large_nested_structure_performance(
        self, parser: MarkdownBinderParser, large_nested_structure: str
    ) -> None:
        """Test parsing performance with large nested structure."""
        # Should parse 1000 items (10*20*5) in under 1 second
        start_time = time.time()
        binder = parser.parse_to_binder(large_nested_structure)
        items = binder.depth_first_traversal()
        end_time = time.time()

        elapsed = end_time - start_time
        assert elapsed < 1.0, f'Parsing took {elapsed:.3f}s, expected < 1.0s'

        # Verify structure - depth_first_traversal returns ALL items, not just roots
        assert len(items) == 1210  # Total items: 10 parts + 200 chapters + 1000 sections
        # Verify the root structure by checking the binder.roots
        assert len(binder.roots) == 10  # 10 parts
        assert len(binder.roots[0].children) == 20  # 20 chapters per part
        assert len(binder.roots[0].children[0].children) == 5  # 5 sections per chapter

        # Count total items - depth_first_traversal already gives us all items
        total_items = len(items)  # This should be 1210

        assert total_items == 10 + (10 * 20) + (10 * 20 * 5)  # 1210 total items

    def test_serialize_large_structure_performance(self, parser: MarkdownBinderParser) -> None:
        """Test serialization performance with large structure."""
        # Create 1000 items programmatically with valid UUIDs
        items = [
            BinderItem(display_title=f'Chapter {i:04d}', node_id=NodeId.generate(), children=[]) for i in range(1000)
        ]
        binder = Binder(roots=items)

        start_time = time.time()
        result = parser.render_from_binder(binder)
        end_time = time.time()

        elapsed = end_time - start_time
        assert elapsed < 1.0, f'Serialization took {elapsed:.3f}s, expected < 1.0s'

        # Verify serialization correctness
        lines = result.split('\n')
        assert len(lines) == 1000
        assert 'Chapter 0000' in lines[0]
        assert 'Chapter 0999' in lines[999]

    def test_roundtrip_large_structure_performance(
        self, parser: MarkdownBinderParser, large_flat_structure: str
    ) -> None:
        """Test roundtrip performance (parse -> serialize -> parse)."""
        start_time = time.time()

        # Parse
        binder = parser.parse_to_binder(large_flat_structure)
        items = binder.roots

        # Serialize
        serialized = parser.render_from_binder(binder)

        # Parse again
        binder2 = parser.parse_to_binder(serialized)
        items2 = binder2.roots

        end_time = time.time()

        elapsed = end_time - start_time
        assert elapsed < 2.0, f'Roundtrip took {elapsed:.3f}s, expected < 2.0s'

        # Verify consistency
        assert len(items) == len(items2) == 1000
        assert items[0].display_title == items2[0].display_title
        assert items[999].display_title == items2[999].display_title

    def test_cli_structure_command_large_project_performance(self, tmp_path: Path) -> None:
        """Test CLI structure command performance with large project."""
        project_dir = tmp_path / 'large_project'
        project_dir.mkdir()

        runner = CliRunner()

        # Initialize project
        runner.invoke(app, ['init', '--title', 'Large Project', '--path', str(project_dir)])

        # Create large structure in binder file manually (faster than CLI)
        binder_path = project_dir / '_binder.md'
        content = binder_path.read_text()

        # Add 500 chapters with valid UUIDs
        from prosemark.domain.models import NodeId

        chapter_entries = []
        for i in range(500):
            node_id = NodeId.generate()
            chapter_entries.append(f'- [Chapter {i:03d}]({node_id}.md)')
        large_structure = '\n'.join(chapter_entries)

        new_content = content.replace('<!-- END_MANAGED_BLOCK -->', f'{large_structure}\n<!-- END_MANAGED_BLOCK -->')
        binder_path.write_text(new_content)

        # Test structure command performance
        start_time = time.time()
        result = runner.invoke(app, ['structure', '--path', str(project_dir)])
        end_time = time.time()

        elapsed = end_time - start_time
        assert elapsed < 1.0, f'Structure command took {elapsed:.3f}s, expected < 1.0s'
        assert result.exit_code == 0

        # Verify all chapters are shown
        output_lines = result.output.split('\n')
        chapter_lines = [line for line in output_lines if 'Chapter' in line]
        assert len(chapter_lines) == 500

    def test_cli_audit_command_large_project_performance(self, tmp_path: Path) -> None:
        """Test CLI audit command performance with large project."""
        project_dir = tmp_path / 'large_audit_project'
        project_dir.mkdir()

        runner = CliRunner()

        # Initialize project
        runner.invoke(app, ['init', '--title', 'Large Audit Project', '--path', str(project_dir)])

        # Create many node files and update binder
        from prosemark.domain.models import NodeId

        binder_entries = []

        for i in range(200):
            # Create node files with valid UUIDs
            node_id = str(NodeId.generate())
            draft_file = project_dir / f'{node_id}.md'
            notes_file = project_dir / f'{node_id}.notes.md'

            draft_content = f"""---
id: {node_id}
title: "Chapter {i:03d}"
created: 2025-09-20T15:30:00Z
updated: 2025-09-20T15:30:00Z
---

# Chapter {i:03d}

Content for chapter {i}.
"""

            notes_content = f"""---
id: {node_id}
title: "Chapter {i:03d}"
created: 2025-09-20T15:30:00Z
updated: 2025-09-20T15:30:00Z
---

# Notes for Chapter {i:03d}

Notes content.
"""

            draft_file.write_text(draft_content)
            notes_file.write_text(notes_content)

            binder_entries.append(f'- [Chapter {i:03d}]({node_id}.md)')

        # Update binder
        binder_path = project_dir / '_binder.md'
        content = binder_path.read_text()
        new_content = content.replace(
            '<!-- END_MANAGED_BLOCK -->', '\n'.join(binder_entries) + '\n<!-- END_MANAGED_BLOCK -->'
        )
        binder_path.write_text(new_content)

        # Test audit command performance
        start_time = time.time()
        result = runner.invoke(app, ['audit', '--path', str(project_dir)])
        end_time = time.time()

        elapsed = end_time - start_time
        assert elapsed < 1.0, f'Audit command took {elapsed:.3f}s, expected < 1.0s'
        assert result.exit_code == 0
        assert 'integrity check completed' in result.output

    def test_memory_usage_large_structure(self, parser: MarkdownBinderParser, large_nested_structure: str) -> None:
        """Test memory usage with large structure (basic check)."""
        import os

        try:
            import psutil
        except ImportError:
            pytest.skip('psutil not available for memory testing')

        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss

        # Parse large structure
        binder = parser.parse_to_binder(large_nested_structure)
        items = binder.depth_first_traversal()

        current_memory = process.memory_info().rss
        memory_increase = current_memory - initial_memory

        # Memory increase should be reasonable (less than 50MB for this structure)
        assert memory_increase < 50 * 1024 * 1024, f'Memory usage too high: {memory_increase / 1024 / 1024:.2f}MB'

        # Verify structure was actually parsed - depth_first_traversal returns all items
        assert len(items) == 1210  # Total items: 10 parts + 200 chapters + 1000 sections

    def test_incremental_structure_building_performance(self, tmp_path: Path) -> None:
        """Test performance of incrementally building large structure."""
        project_dir = tmp_path / 'incremental_project'
        project_dir.mkdir()

        runner = CliRunner()
        runner.invoke(app, ['init', '--title', 'Incremental Project', '--path', str(project_dir)])

        # Time adding 100 chapters
        start_time = time.time()

        for i in range(100):
            result = runner.invoke(app, ['add', f'Chapter {i:03d}', '--path', str(project_dir)])
            assert result.exit_code == 0

        end_time = time.time()
        elapsed = end_time - start_time

        # Should add 100 chapters in reasonable time (allowing for CLI overhead)
        assert elapsed < 30.0, f'Adding 100 chapters took {elapsed:.3f}s, expected < 30.0s'

        # Verify all chapters were added
        result = runner.invoke(app, ['structure', '--path', str(project_dir)])
        assert result.exit_code == 0
        chapter_lines = [line for line in result.output.split('\n') if 'Chapter' in line]
        assert len(chapter_lines) == 100

    def test_search_performance_in_large_structure(
        self, parser: MarkdownBinderParser, large_nested_structure: str
    ) -> None:
        """Test performance of searching in large structure."""
        binder = parser.parse_to_binder(large_nested_structure)
        items = binder.depth_first_traversal()

        # Simulate searching for specific items by title
        start_time = time.time()

        found_items = []
        search_terms = ['Part 05', 'Chapter 3.10', 'Section 7.15.2']

        def search_items(items_list: list[BinderItem], term: str) -> list[BinderItem]:
            """Recursively search for items by title."""
            results = []
            for item in items_list:
                if term in item.display_title:
                    results.append(item)
                results.extend(search_items(item.children, term))
            return results

        for term in search_terms:
            found = search_items(items, term)
            found_items.extend(found)

        end_time = time.time()
        elapsed = end_time - start_time

        # Search should be fast even in large structure
        assert elapsed < 0.1, f'Search took {elapsed:.3f}s, expected < 0.1s'
        assert len(found_items) > 0  # Should find at least some items
