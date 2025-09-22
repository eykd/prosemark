"""Performance tests for file I/O operations."""

import time
from datetime import UTC, datetime
from pathlib import Path
from typing import TYPE_CHECKING

import pytest
from typer.testing import CliRunner

from prosemark.adapters.binder_repo_fs import BinderRepoFs
from prosemark.adapters.node_repo_fs import NodeRepoFs
from prosemark.cli.main import app
from prosemark.domain.entities import Node
from prosemark.domain.models import Binder, BinderItem, NodeId
from prosemark.exceptions import FileSystemError

if TYPE_CHECKING:
    from prosemark.ports.clock import Clock
    from prosemark.ports.editor_port import EditorPort


class TestFileOperationsPerformance:
    """Test performance of file I/O operations."""

    @pytest.fixture
    def binder_repo(self, tmp_path: Path) -> BinderRepoFs:
        """Create a file system binder repository."""
        return BinderRepoFs(project_path=tmp_path)

    @pytest.fixture
    def node_repo(self, tmp_path: Path) -> NodeRepoFs:
        """Create a file system node repository."""
        from prosemark.adapters.editor_launcher_system import EditorLauncherSystem
        from prosemark.adapters.fake_clock import FakeClock

        editor: EditorPort = EditorLauncherSystem()
        clock: Clock = FakeClock()
        return NodeRepoFs(project_path=tmp_path, editor=editor, clock=clock)

    @pytest.fixture
    def test_node(self) -> Node:
        """Create a test node for operations."""
        # Create a proper UUIDv7 for testing
        node_id = NodeId.generate()
        return Node(
            node_id=node_id,
            title='Test Chapter',
            synopsis='A test chapter for performance testing',
            created=datetime.now(UTC),
            updated=datetime.now(UTC),
            draft_path=Path(f'{node_id}.md'),
            notes_path=Path(f'{node_id}.notes.md'),
        )

    def test_node_create_performance(self, node_repo: NodeRepoFs, test_node: Node, tmp_path: Path) -> None:
        """Test node create operation performance."""
        # Should create node files in under 100ms
        start_time = time.time()
        node_repo.create(test_node.id, test_node.title, test_node.synopsis)
        end_time = time.time()

        elapsed = end_time - start_time
        assert elapsed < 0.1, f'Node create took {elapsed:.3f}s, expected < 0.1s'

        # Verify files were created
        draft_file = tmp_path / f'{test_node.id}.md'
        notes_file = tmp_path / f'{test_node.id}.notes.md'
        assert draft_file.exists()
        assert notes_file.exists()

    def test_node_read_performance(self, node_repo: NodeRepoFs, test_node: Node, tmp_path: Path) -> None:
        """Test node read frontmatter operation performance."""
        # First create the node
        node_repo.create(test_node.id, test_node.title, test_node.synopsis)

        # Then test read performance
        start_time = time.time()
        frontmatter = node_repo.read_frontmatter(test_node.id)
        end_time = time.time()

        elapsed = end_time - start_time
        assert elapsed < 0.1, f'Node read took {elapsed:.3f}s, expected < 0.1s'

        # Verify loaded frontmatter is correct
        assert frontmatter['id'] == str(test_node.id)
        assert frontmatter['title'] == test_node.title

    def test_multiple_node_operations_performance(self, node_repo: NodeRepoFs, tmp_path: Path) -> None:
        """Test performance of multiple node operations."""
        # Create 50 nodes
        nodes = []
        for i in range(50):
            node_id = NodeId.generate()
            node = Node(
                node_id=node_id,
                title=f'Chapter {i:02d}',
                synopsis=f'Synopsis for chapter {i}',
                created=datetime.now(UTC),
                updated=datetime.now(UTC),
                draft_path=Path(f'{node_id}.md'),
                notes_path=Path(f'{node_id}.notes.md'),
            )
            nodes.append(node)

        # Test batch create performance
        start_time = time.time()
        for node in nodes:
            node_repo.create(node.id, node.title, node.synopsis)
        end_time = time.time()

        create_elapsed = end_time - start_time
        assert create_elapsed < 5.0, f'Creating 50 nodes took {create_elapsed:.3f}s, expected < 5.0s'

        # Test batch read performance
        start_time = time.time()
        loaded_frontmatters = []
        for node in nodes:
            frontmatter = node_repo.read_frontmatter(node.id)
            loaded_frontmatters.append(frontmatter)
        end_time = time.time()

        read_elapsed = end_time - start_time
        assert read_elapsed < 2.0, f'Reading 50 nodes took {read_elapsed:.3f}s, expected < 2.0s'

        # Verify all nodes read correctly
        assert len(loaded_frontmatters) == 50
        for i, frontmatter in enumerate(loaded_frontmatters):
            assert frontmatter['title'] == f'Chapter {i:02d}'

    def test_binder_save_performance(self, binder_repo: BinderRepoFs, tmp_path: Path) -> None:
        """Test binder save operation performance."""
        # Create a binder with many items
        items = [
            BinderItem(display_title=f'Chapter {i:02d}', node_id=NodeId.generate(), children=[]) for i in range(100)
        ]

        binder = Binder(roots=items)

        # Test save performance
        start_time = time.time()
        binder_repo.save(binder)
        end_time = time.time()

        elapsed = end_time - start_time
        assert elapsed < 0.1, f'Binder save took {elapsed:.3f}s, expected < 0.1s'

        # Verify binder file was created
        binder_file = tmp_path / '_binder.md'
        assert binder_file.exists()

    def test_binder_load_performance(self, binder_repo: BinderRepoFs, tmp_path: Path) -> None:
        """Test binder load operation performance."""
        # Create and save a large binder
        items = [
            BinderItem(display_title=f'Chapter {i:02d}', node_id=NodeId.generate(), children=[]) for i in range(100)
        ]

        binder = Binder(roots=items)

        binder_repo.save(binder)

        # Test load performance
        start_time = time.time()
        loaded_binder = binder_repo.load()
        end_time = time.time()

        elapsed = end_time - start_time
        assert elapsed < 0.1, f'Binder load took {elapsed:.3f}s, expected < 0.1s'

        # Verify loaded data
        assert len(loaded_binder.roots) == 100

    def test_large_file_content_performance(self, node_repo: NodeRepoFs, tmp_path: Path) -> None:
        """Test performance with large file content."""
        # Create a node with large content
        large_content = '# Large Chapter\n\n' + ('This is a test line with substantial content. ' * 1000)

        node_id = NodeId.generate()
        node = Node(
            node_id=node_id,
            title='Large Chapter',
            synopsis='A chapter with large content',
            created=datetime.now(UTC),
            updated=datetime.now(UTC),
            draft_path=Path(f'{node_id}.md'),
            notes_path=Path(f'{node_id}.notes.md'),
        )

        # Test create performance with large content simulation
        start_time = time.time()
        node_repo.create(node.id, node.title, node.synopsis)

        # Manually add large content to simulate large file
        draft_file = tmp_path / f'{node.id}.md'
        content = draft_file.read_text()
        large_file_content = content + '\n\n' + large_content
        draft_file.write_text(large_file_content)

        end_time = time.time()
        create_elapsed = end_time - start_time

        # Should handle large content reasonably
        assert create_elapsed < 0.5, f'Large file create took {create_elapsed:.3f}s, expected < 0.5s'

        # Test read performance with large content
        start_time = time.time()
        frontmatter = node_repo.read_frontmatter(node.id)
        end_time = time.time()

        read_elapsed = end_time - start_time
        assert read_elapsed < 0.5, f'Large file read took {read_elapsed:.3f}s, expected < 0.5s'

        # Verify frontmatter read correctly
        assert frontmatter['title'] == 'Large Chapter'

    def test_concurrent_file_operations_simulation(self, node_repo: NodeRepoFs, tmp_path: Path) -> None:
        """Test simulated concurrent file operations."""
        import queue
        import threading

        result_queue: queue.Queue[tuple[int, list[tuple[float, float]] | str]] = queue.Queue()
        num_threads = 5
        nodes_per_thread = 10

        def thread_operations(thread_id: int) -> None:
            """Perform file operations in a thread."""
            try:
                thread_times = []
                for i in range(nodes_per_thread):
                    node_id = NodeId.generate()
                    node = Node(
                        node_id=node_id,
                        title=f'Thread {thread_id} Node {i}',
                        synopsis=f'Node {i} from thread {thread_id}',
                        created=datetime.now(UTC),
                        updated=datetime.now(UTC),
                        draft_path=Path(f'{node_id}.md'),
                        notes_path=Path(f'{node_id}.notes.md'),
                    )

                    # Time create operation
                    start = time.time()
                    node_repo.create(node.id, node.title, node.synopsis)
                    create_time = time.time() - start

                    # Time read operation
                    start = time.time()
                    node_repo.read_frontmatter(node.id)
                    read_time = time.time() - start

                    thread_times.append((create_time, read_time))

                result_queue.put((thread_id, thread_times))
            except (FileSystemError, OSError) as e:
                result_queue.put((thread_id, f'Error: {e}'))

        # Start threads
        threads = []
        start_time = time.time()

        for thread_id in range(num_threads):
            thread = threading.Thread(target=thread_operations, args=(thread_id,))
            threads.append(thread)
            thread.start()

        # Wait for completion
        for thread in threads:
            thread.join()

        end_time = time.time()
        total_elapsed = end_time - start_time

        # Collect results
        all_times = []
        while not result_queue.empty():
            thread_id, times = result_queue.get()
            if isinstance(times, str):  # Error case
                pytest.fail(f'Thread {thread_id} failed: {times}')
            all_times.extend(times)

        # Verify performance
        num_threads * nodes_per_thread * 2  # create + read
        assert total_elapsed < 10.0, f'Concurrent operations took {total_elapsed:.3f}s, expected < 10.0s'

        # Verify all operations completed
        assert len(all_times) == num_threads * nodes_per_thread

        # Check individual operation times
        max_create_time = max(times[0] for times in all_times)
        max_read_time = max(times[1] for times in all_times)

        assert max_create_time < 1.0, f'Slowest create took {max_create_time:.3f}s'
        assert max_read_time < 1.0, f'Slowest read took {max_read_time:.3f}s'

    def test_cli_command_response_times(self, tmp_path: Path) -> None:
        """Test CLI command response times."""
        project_dir = tmp_path / 'perf_project'
        project_dir.mkdir()

        runner = CliRunner()

        # Test init command
        start_time = time.time()
        result = runner.invoke(app, ['init', '--title', 'Perf Test', '--path', str(project_dir)])
        init_time = time.time() - start_time

        assert result.exit_code == 0
        assert init_time < 1.0, f'Init command took {init_time:.3f}s, expected < 1.0s'

        # Test add command
        start_time = time.time()
        result = runner.invoke(app, ['add', 'Test Chapter', '--path', str(project_dir)])
        add_time = time.time() - start_time

        assert result.exit_code == 0
        assert add_time < 1.0, f'Add command took {add_time:.3f}s, expected < 1.0s'

        # Test structure command
        start_time = time.time()
        result = runner.invoke(app, ['structure', '--path', str(project_dir)])
        structure_time = time.time() - start_time

        assert result.exit_code == 0
        assert structure_time < 1.0, f'Structure command took {structure_time:.3f}s, expected < 1.0s'

        # Test audit command
        start_time = time.time()
        result = runner.invoke(app, ['audit', '--path', str(project_dir)])
        audit_time = time.time() - start_time

        assert result.exit_code == 0
        assert audit_time < 1.0, f'Audit command took {audit_time:.3f}s, expected < 1.0s'

    def test_file_system_stress_test(self, node_repo: NodeRepoFs, tmp_path: Path) -> None:
        """Test file system operations under stress."""
        # Create many files quickly
        num_files = 200
        created_node_ids = []

        start_time = time.time()

        for i in range(num_files):
            node_id = NodeId.generate()
            created_node_ids.append(node_id)
            node = Node(
                node_id=node_id,
                title=f'Stress Test Node {i}',
                synopsis=f'Node {i} for stress testing',
                created=datetime.now(UTC),
                updated=datetime.now(UTC),
                draft_path=Path(f'{node_id}.md'),
                notes_path=Path(f'{node_id}.notes.md'),
            )
            node_repo.create(node.id, node.title, node.synopsis)

        creation_time = time.time() - start_time

        # Should create files reasonably quickly
        assert creation_time < 20.0, f'Creating {num_files} files took {creation_time:.3f}s, expected < 20.0s'

        # Verify all files exist
        draft_files = list(tmp_path.glob('*.md'))
        notes_files = list(tmp_path.glob('*.notes.md'))

        # Should have draft files and notes files
        assert len(draft_files) >= num_files
        assert len(notes_files) >= num_files

        # Test random access performance
        import random

        random_node_ids = random.sample(created_node_ids, 20)

        start_time = time.time()
        for node_id in random_node_ids:
            frontmatter = node_repo.read_frontmatter(node_id)
            # Just verify we can read the node - title will have index that we don't know
            assert 'title' in frontmatter
            assert frontmatter['title'].startswith('Stress Test Node')

        random_access_time = time.time() - start_time
        assert random_access_time < 2.0, f'Random access took {random_access_time:.3f}s, expected < 2.0s'

    def test_disk_space_efficiency(self, node_repo: NodeRepoFs, binder_repo: BinderRepoFs, tmp_path: Path) -> None:
        """Test that operations are disk space efficient."""
        # Measure initial disk usage
        initial_size = sum(f.stat().st_size for f in tmp_path.rglob('*') if f.is_file())

        # Create project with moderate content
        items = []
        for i in range(20):
            node_id = NodeId.generate()
            node = Node(
                node_id=node_id,
                title=f'Chapter {i:02d}',
                synopsis=f'Synopsis for chapter {i}',
                created=datetime.now(UTC),
                updated=datetime.now(UTC),
                draft_path=Path(f'{node_id}.md'),
                notes_path=Path(f'{node_id}.notes.md'),
            )
            node_repo.create(node.id, node.title, node.synopsis)

            items.append(BinderItem(display_title=f'Chapter {i:02d}', node_id=node.id, children=[]))

        binder = Binder(roots=items)
        binder_repo.save(binder)

        # Measure final disk usage
        final_size = sum(f.stat().st_size for f in tmp_path.rglob('*') if f.is_file())
        project_size = final_size - initial_size

        # Project should be reasonably sized (less than 100KB for 20 chapters)
        assert project_size < 100 * 1024, f'Project uses {project_size} bytes, expected < 100KB'

        # Verify all expected files exist
        expected_files = 20 * 2 + 1  # 20 * (draft + notes) + binder
        actual_files = len(list(tmp_path.rglob('*.md')))
        assert actual_files == expected_files
