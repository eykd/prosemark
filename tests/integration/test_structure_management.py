"""Integration test for binder structure management."""

from pathlib import Path
from typing import Any

import pytest
from typer.testing import CliRunner

from prosemark.cli.main import app


class TestStructureManagement:
    """Test binder structure management operations."""

    @pytest.fixture
    def runner(self) -> CliRunner:
        """Create a CLI runner for testing."""
        return CliRunner()

    @pytest.fixture
    def complex_project(self, tmp_path: Path) -> dict[str, Any]:
        """Create a project with complex hierarchy."""
        project_dir = tmp_path / 'complex_project'
        project_dir.mkdir()

        runner = CliRunner()
        runner.invoke(app, ['init', '--title', 'Complex Project', '--path', str(project_dir)])

        # Create a complex structure
        # Part 1
        result = runner.invoke(app, ['add', 'Part 1', '--path', str(project_dir)])
        part1_id = self._extract_node_id(result.output)

        # Chapters under Part 1
        result = runner.invoke(app, ['add', 'Chapter 1', '--parent', part1_id, '--path', str(project_dir)])
        ch1_id = self._extract_node_id(result.output)

        result = runner.invoke(app, ['add', 'Chapter 2', '--parent', part1_id, '--path', str(project_dir)])
        ch2_id = self._extract_node_id(result.output)

        # Sections under Chapter 1
        runner.invoke(app, ['add', 'Section 1.1', '--parent', ch1_id, '--path', str(project_dir)])
        runner.invoke(app, ['add', 'Section 1.2', '--parent', ch1_id, '--path', str(project_dir)])

        # Part 2
        result = runner.invoke(app, ['add', 'Part 2', '--path', str(project_dir)])
        part2_id = self._extract_node_id(result.output)

        # Chapter under Part 2
        result = runner.invoke(app, ['add', 'Chapter 3', '--parent', part2_id, '--path', str(project_dir)])
        ch3_id = self._extract_node_id(result.output)

        return {
            'dir': project_dir,
            'part1_id': part1_id,
            'part2_id': part2_id,
            'ch1_id': ch1_id,
            'ch2_id': ch2_id,
            'ch3_id': ch3_id,
        }

    def _extract_node_id(self, output: str) -> str:
        """Extract node ID from add command output."""
        lines = output.split('\n')
        added_line = next(line for line in lines if 'Added' in line)
        return added_line.split('(')[1].split(')')[0]

    def test_view_complex_structure(self, runner: CliRunner, complex_project: dict[str, Any]) -> None:
        """Test viewing a complex hierarchical structure."""
        result = runner.invoke(app, ['structure', '--path', str(complex_project['dir'])])
        assert result.exit_code == 0

        # Verify all parts are shown
        assert 'Part 1' in result.output
        assert 'Part 2' in result.output
        assert 'Chapter 1' in result.output
        assert 'Chapter 2' in result.output
        assert 'Chapter 3' in result.output
        assert 'Section 1.1' in result.output
        assert 'Section 1.2' in result.output

        # Verify hierarchy is correct (indentation)
        lines = result.output.split('\n')
        part1_line = next(i for i, line in enumerate(lines) if 'Part 1' in line)
        ch1_line = next(i for i, line in enumerate(lines) if 'Chapter 1' in line)
        sec11_line = next(i for i, line in enumerate(lines) if 'Section 1.1' in line)

        # Chapters should be indented more than parts
        assert lines[ch1_line].index('Chapter') > lines[part1_line].index('Part')
        # Sections should be indented more than chapters
        assert lines[sec11_line].index('Section') > lines[ch1_line].index('Chapter')

    def test_move_between_parents(self, runner: CliRunner, complex_project: dict[str, Any]) -> None:
        """Test moving nodes between different parents."""
        # Move Chapter 2 from Part 1 to Part 2
        result = runner.invoke(
            app,
            [
                'move',
                complex_project['ch2_id'],
                '--parent',
                complex_project['part2_id'],
                '--path',
                str(complex_project['dir']),
            ],
        )
        assert result.exit_code == 0

        # Verify the move
        result = runner.invoke(app, ['structure', '--path', str(complex_project['dir'])])

        # Chapter 2 should now be under Part 2
        lines = result.output.split('\n')
        part2_idx = next(i for i, line in enumerate(lines) if 'Part 2' in line)
        ch2_idx = next(i for i, line in enumerate(lines) if 'Chapter 2' in line)
        ch3_idx = next(i for i, line in enumerate(lines) if 'Chapter 3' in line)

        # Chapter 2 should appear between Part 2 and after it (under Part 2)
        assert part2_idx < ch2_idx
        # Both chapters should be at same indentation level
        assert lines[ch2_idx].index('Chapter 2') == lines[ch3_idx].index('Chapter 3')

    def test_move_to_root_level(self, runner: CliRunner, complex_project: dict[str, Any]) -> None:
        """Test moving a nested node to root level."""
        # Move Chapter 1 to root level
        result = runner.invoke(app, ['move', complex_project['ch1_id'], '--path', str(complex_project['dir'])])
        assert result.exit_code == 0

        # Verify Chapter 1 is now at root
        result = runner.invoke(app, ['structure', '--path', str(complex_project['dir'])])

        lines = result.output.split('\n')
        ch1_line = next(line for line in lines if 'Chapter 1' in line)
        part1_line = next(line for line in lines if 'Part 1' in line)

        # Chapter 1 should be at same indentation as Part 1 (both root level)
        assert ch1_line.index('Chapter 1') == part1_line.index('Part 1')

    def test_remove_node_with_children_promotes_children(
        self, runner: CliRunner, complex_project: dict[str, Any]
    ) -> None:
        """Test removing a node promotes its children to parent level."""
        # Remove Part 1 (which has chapters and sections)
        result = runner.invoke(app, ['remove', complex_project['part1_id'], '--path', str(complex_project['dir'])])
        assert result.exit_code == 0

        # Verify Part 1 is gone but its children are promoted to root level
        result = runner.invoke(app, ['structure', '--path', str(complex_project['dir'])])

        assert 'Part 1' not in result.output
        # Children should be promoted to root level
        assert 'Chapter 1' in result.output
        assert 'Chapter 2' in result.output
        assert 'Section 1.1' in result.output
        assert 'Section 1.2' in result.output

        # Part 2 should still exist
        assert 'Part 2' in result.output
        assert 'Chapter 3' in result.output

    def test_remove_node_keep_children(self, runner: CliRunner, complex_project: dict[str, Any]) -> None:
        """Test removing a node while keeping its children."""
        # Remove Part 1 but keep its chapters (default behavior promotes children)
        result = runner.invoke(app, ['remove', complex_project['part1_id'], '--path', str(complex_project['dir'])])
        assert result.exit_code == 0

        # Verify Part 1 is gone but chapters are promoted to root
        result = runner.invoke(app, ['structure', '--path', str(complex_project['dir'])])

        assert 'Part 1' not in result.output
        # Chapters should now be at root level
        assert 'Chapter 1' in result.output
        assert 'Chapter 2' in result.output
        # Sections should still be under Chapter 1
        assert 'Section 1.1' in result.output
        assert 'Section 1.2' in result.output

    def test_position_ordering(self, runner: CliRunner, complex_project: dict[str, Any]) -> None:
        """Test adding nodes at specific positions."""
        # Add a new part at position 0 (beginning)
        result = runner.invoke(app, ['add', 'Part 0', '--position', '0', '--path', str(complex_project['dir'])])
        assert result.exit_code == 0

        # Verify it's first
        result = runner.invoke(app, ['structure', '--path', str(complex_project['dir'])])

        lines = [line for line in result.output.split('\n') if line.strip()]
        # First content line should be Part 0
        first_part = next(line for line in lines if 'Part' in line)
        assert 'Part 0' in first_part

    def test_circular_reference_prevention(self, runner: CliRunner, complex_project: dict[str, Any]) -> None:
        """Test that circular references are prevented."""
        # Try to move Part 1 under Chapter 1 (its own child)
        result = runner.invoke(
            app,
            [
                'move',
                complex_project['part1_id'],
                '--parent',
                complex_project['ch1_id'],
                '--path',
                str(complex_project['dir']),
            ],
        )

        # Should fail or show error
        assert 'circular' in result.output.lower() or result.exit_code != 0
