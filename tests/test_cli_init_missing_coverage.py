"""Tests to cover missing lines in CLI init command."""

from pathlib import Path
from unittest.mock import Mock, patch

from click.testing import CliRunner

from prosemark.cli.init import FileSystemConfigPort, init_command


class TestInitMissingCoverage:
    """Test missing coverage lines in init command."""

    def test_filesystem_config_port_config_exists(self, tmp_path: Path) -> None:
        """Test FileSystemConfigPort.config_exists method (line 26)."""
        config_port = FileSystemConfigPort()

        # Test with existing file
        existing_file = tmp_path / 'config.toml'
        existing_file.write_text('test')
        assert config_port.config_exists(existing_file) is True

        # Test with non-existing file
        non_existing_file = tmp_path / 'nonexistent.toml'
        assert config_port.config_exists(non_existing_file) is False

    def test_filesystem_config_port_get_default_config_values(self) -> None:
        """Test FileSystemConfigPort.get_default_config_values method (line 30)."""
        config_port = FileSystemConfigPort()
        result = config_port.get_default_config_values()
        assert result == {}

    def test_filesystem_config_port_load_config(self) -> None:
        """Test FileSystemConfigPort.load_config method (line 34)."""
        config_port = FileSystemConfigPort()
        result = config_port.load_config()
        assert result == {}

        # Test with path parameter
        result = config_port.load_config(Path('test.toml'))
        assert result == {}

    def test_init_command_general_exception_handling(self) -> None:
        """Test init command handles general exceptions (lines 72-74)."""
        runner = CliRunner()

        with runner.isolated_filesystem(), patch('prosemark.cli.init.InitProject') as mock_init_project:
            mock_instance = Mock()
            mock_instance.execute.side_effect = ValueError('Test error')
            mock_init_project.return_value = mock_instance

            result = runner.invoke(init_command, ['--title', 'Test Project'])

            assert result.exit_code == 3
            assert 'Unexpected error: Test error' in result.output
