"""Pytest configuration file for Prosemark tests."""

import sys
from collections.abc import Generator
from pathlib import Path
from unittest.mock import patch

import pytest
from click.testing import CliRunner

from prosemark.domain.nodes import Node, NodeID
from prosemark.repositories.project import ProjectRepository
from prosemark.storages.filesystem import FilesystemMdNodeStorage
from prosemark.storages.inmemory import InMemoryNodeStorage

# Add the src directory to the Python path
src_path = Path(__file__).parent.parent / 'src'
sys.path.insert(0, str(src_path))


@pytest.fixture
def runner(tmp_path: Path) -> Generator[CliRunner, None, None]:
    """Create a CLI test runner."""
    runner = CliRunner()
    with runner.isolated_filesystem(temp_dir=tmp_path):
        yield runner


@pytest.fixture
def runner_path(runner: CliRunner) -> Path:
    """Fixture to create a temporary directory for CLI tests."""
    return Path.cwd()


@pytest.fixture
def node_ids() -> Generator[list[NodeID], None, None]:
    """Fixture to generate unique node IDs."""
    start_id = 202501020304050600
    node_ids = [str(n) for n in range(start_id, start_id + 1000)]
    with patch.object(Node, 'generate_id', side_effect=node_ids):
        yield node_ids


@pytest.fixture
def fs_storage(runner_path: Path) -> FilesystemMdNodeStorage:
    """Fixture to create a FilesystemMdNodeStorage instance."""
    return FilesystemMdNodeStorage(runner_path)


@pytest.fixture
def fs_project_repository(fs_storage: FilesystemMdNodeStorage) -> ProjectRepository:
    """Fixture to create a ProjectRepository instance."""
    return ProjectRepository(fs_storage)


@pytest.fixture
def mem_storage() -> InMemoryNodeStorage:
    """Fixture to create an InMemoryNodeStorage instance."""
    return InMemoryNodeStorage()


@pytest.fixture
def mem_project_repository(mem_storage: InMemoryNodeStorage) -> ProjectRepository:
    """Fixture to create a ProjectRepository instance."""
    return ProjectRepository(mem_storage)
