"""Integration tests for CLI --list-templates command."""

from pathlib import Path

from click.testing import CliRunner

from prosemark.cli.add import add_command


class TestCLIListTemplates:
    """Test CLI --list-templates functionality."""

    def test_list_templates_no_directory(self, tmp_path: Path) -> None:
        """Test --list-templates when no templates directory exists."""
        runner = CliRunner()
        with runner.isolated_filesystem(temp_dir=tmp_path):
            result = runner.invoke(add_command, ['dummy-title', '--list-templates'])

            assert result.exit_code == 0
            assert 'No templates directory found' in result.output

    def test_list_templates_empty_directory(self, tmp_path: Path) -> None:
        """Test --list-templates with empty templates directory."""
        templates_dir = tmp_path / 'templates'
        templates_dir.mkdir()

        runner = CliRunner()
        with runner.isolated_filesystem(temp_dir=tmp_path):
            result = runner.invoke(add_command, ['dummy-title', '--list-templates', '--path', str(tmp_path)])

            assert result.exit_code == 0
            assert 'No templates found' in result.output

    def test_list_templates_with_single_templates(self, tmp_path: Path) -> None:
        """Test --list-templates displays single templates."""
        templates_dir = tmp_path / 'templates'
        templates_dir.mkdir()

        # Create single template
        template = templates_dir / 'meeting-notes.md'
        template.write_text('---\ntitle: "{{title}}"\n---\n\n# {{title}}\n\nContent here.')

        runner = CliRunner()
        with runner.isolated_filesystem(temp_dir=tmp_path):
            result = runner.invoke(add_command, ['dummy-title', '--list-templates', '--path', str(tmp_path)])

            assert result.exit_code == 0
            assert 'Found 1 template(s):' in result.output
            assert 'Single templates:' in result.output
            assert 'meeting-notes' in result.output

    def test_list_templates_with_directory_templates(self, tmp_path: Path) -> None:
        """Test --list-templates displays directory templates."""
        templates_dir = tmp_path / 'templates'
        templates_dir.mkdir()

        # Create directory template
        project_dir = templates_dir / 'project-setup'
        project_dir.mkdir()
        overview = project_dir / 'overview.md'
        overview.write_text('---\ntitle: "Overview"\n---\n\n# Overview')

        runner = CliRunner()
        with runner.isolated_filesystem(temp_dir=tmp_path):
            result = runner.invoke(add_command, ['dummy-title', '--list-templates', '--path', str(tmp_path)])

            assert result.exit_code == 0
            assert 'Found 1 template(s):' in result.output
            assert 'Directory templates:' in result.output
            assert 'project-setup' in result.output

    def test_list_templates_with_both_types(self, tmp_path: Path) -> None:
        """Test --list-templates displays both single and directory templates."""
        templates_dir = tmp_path / 'templates'
        templates_dir.mkdir()

        # Create single template
        single = templates_dir / 'simple.md'
        single.write_text('---\ntitle: "{{title}}"\n---\n\nContent')

        # Create directory template
        project_dir = templates_dir / 'project'
        project_dir.mkdir()
        overview = project_dir / 'main.md'
        overview.write_text('---\ntitle: "Main"\n---\n\nMain content')

        runner = CliRunner()
        with runner.isolated_filesystem(temp_dir=tmp_path):
            result = runner.invoke(add_command, ['dummy-title', '--list-templates', '--path', str(tmp_path)])

            assert result.exit_code == 0
            assert 'Found 2 template(s):' in result.output
            assert 'Single templates:' in result.output
            assert 'simple' in result.output
            assert 'Directory templates:' in result.output
            assert 'project' in result.output
