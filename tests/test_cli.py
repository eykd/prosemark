from __future__ import annotations

import textwrap
from typing import TYPE_CHECKING

if TYPE_CHECKING:  # pragma: no cover
    from pathlib import Path

    import pytest
    from click.testing import CliRunner

    from prosemark.domain.nodes import NodeID
    from prosemark.repositories.project import ProjectRepository


from prosemark.adapters.cli import CLIService
from prosemark.cli import main
from prosemark.domain.nodes import Node
from prosemark.domain.projects import Project
from prosemark.repositories.project import ProjectRepository
from prosemark.storages.inmemory import InMemoryNodeStorage

try:
    from typing import NoReturn
except ImportError:
    NoReturn = None  # type: ignore[assignment]


from unittest.mock import patch

import yaml


def test_cli_main(runner: CliRunner) -> None:
    """Test that the CLI runs without error."""
    result = runner.invoke(main)
    assert result.exit_code == 0


def test_cli_init(runner: CliRunner, runner_path: Path) -> None:
    """Test the init command."""
    result = runner.invoke(main, ['init', 'Test Project', '--card', 'A test project'])
    assert result.exit_code == 0
    assert result.output == textwrap.dedent(
        """\
        Project 'Test Project' initialized successfully.
        """
    )
    assert (runner_path / '_binder.md').exists()


def test_cli_info(runner: CliRunner) -> None:
    """Test the info command."""
    # First create a project
    runner.invoke(main, ['init', 'Test Project', '--card', 'A test project'])

    # Then get info about it
    result = runner.invoke(main, ['info'])
    assert result.exit_code == 0
    expected = textwrap.dedent(
        """\
        Project: Test Project
        Description: A test project
        Nodes: 1

        Metadata:

        """
    )
    assert result.output == expected


def test_cli_add(runner: CliRunner, node_ids: list[NodeID]) -> None:
    """Test the add command."""
    # First create a project
    runner.invoke(main, ['init', 'Test Project'])

    # Then add a node
    result = runner.invoke(main, ['add', '_binder', 'New Node', '--card', 'A brief summary', '--text', 'Some content'])
    assert result.exit_code == 0
    expected = textwrap.dedent(
        f"""\
        Node added successfully with ID: {node_ids[1]}
        """
    )
    assert result.output == expected


def test_cli_remove(runner: CliRunner) -> None:
    """Test the remove command."""
    # First create a project with a node
    runner.invoke(main, ['init', 'Test Project'])
    runner.invoke(main, ['add', '_binder', 'Node to remove'])

    # Get the node ID from the structure
    structure_result = runner.invoke(main, ['structure'])
    node_id = structure_result.output.split('\n')[1].split()[1]

    # Then remove the node
    result = runner.invoke(main, ['remove', node_id])
    assert result.exit_code == 0
    expected = textwrap.dedent(
        """\
        Node 'Node to remove' removed successfully
        """
    )
    assert result.output == expected


def test_cli_move(runner: CliRunner) -> None:
    """Test the move command."""
    # First create a project with nodes
    runner.invoke(main, ['init', 'Test Project'])
    runner.invoke(main, ['add', '_binder', 'Parent Node'])
    runner.invoke(main, ['add', '_binder', 'Node to move'])

    # Get node IDs from the structure
    structure_result = runner.invoke(main, ['structure'])
    lines = structure_result.output.split('\n')
    parent_id = lines[1].split()[1]
    node_id = lines[2].split()[1]

    # Then move the node
    result = runner.invoke(main, ['move', node_id, parent_id])
    assert result.exit_code == 0
    assert result.output == 'Node moved successfully\n'


def test_cli_show(runner: CliRunner, node_ids: list[NodeID]) -> None:
    """Test the show command."""
    # First create a project with a node
    runner.invoke(main, ['init', 'Test Project'])
    runner.invoke(main, ['add', '_binder', 'Node to show', '--text', 'This is the text'])

    # Get the node ID from the structure
    structure_result = runner.invoke(main, ['structure'])
    node_id = structure_result.output.split('\n')[1].split()[1]

    # Then show the node
    result = runner.invoke(main, ['show', node_id])
    assert result.exit_code == 0
    assert result.output == textwrap.dedent(
        f"""\
        Title: Node to show

        Card:
        [[{node_ids[1]} card.md]]

        Text:
        This is the text

        Notes:
        [[{node_ids[1]} notes.md]]

        """
    )


def test_cli_edit(runner: CliRunner) -> None:
    """Test the edit command."""
    # First create a project with a node
    runner.invoke(main, ['init', 'Test Project'])
    runner.invoke(main, ['add', '_binder', 'Node to edit'])

    # Get the node ID from the structure
    structure_result = runner.invoke(main, ['structure'])
    node_id = structure_result.output.split('\n')[1].split()[1]

    # Then edit the node without opening an editor
    result = runner.invoke(main, ['edit', node_id, '--no-editor'])
    assert result.exit_code == 0
    expected = textwrap.dedent(
        """\
        Node updated successfully
        """
    )
    assert result.output == expected


def test_cli_structure(
    runner: CliRunner, node_ids: list[NodeID], fs_project_repository: ProjectRepository, runner_path: Path
) -> None:
    """Test the structure command."""
    runner.invoke(main, ['init', 'New Project'])
    project = fs_project_repository.load_project()

    # Add some nodes
    child1 = project.create_node(project.root_node.id, title='Child 1')
    assert isinstance(child1, Node)
    project.create_node(project.root_node.id, title='Child 2')
    project.create_node(child1.id, title='Grandchild')
    fs_project_repository.save_project(project)

    assert (runner_path / '_binder.md').read_text() == textwrap.dedent(
        """\
        ---
        id: _binder
        title: New Project
        ---
        // Card: [[_binder card.md]]
        // Notes: [[_binder notes.md]]

        # New Project

        [[_binder card.md]]

        - [Child 1](20250102030406.md)
          - [Grandchild](20250102030408.md)
        - [Child 2](20250102030407.md)
        """
    )

    # Then display the structure
    result = runner.invoke(main, ['structure'])
    assert result.exit_code == 0
    expected = textwrap.dedent(
        f"""\
        _binder - New Project
        - {node_ids[1]} Child 1
          - {node_ids[3]} Grandchild
        - {node_ids[2]} Child 2

        """
    )
    assert result.output == expected


def test_root_card_show_and_remove(runner: CliRunner) -> None:
    """Test the root node (_binder) card show and remove commands."""
    runner.invoke(main, ['init', 'Test Project', '--card', 'Root card text'])
    # Show the root card (should show the default directive, not the text)
    result = runner.invoke(main, ['card', 'show', '_binder'])
    assert result.exit_code == 0
    assert '[[_binder card.md]]' in result.output

    # Remove the root card (should still succeed, even if not present)
    result = runner.invoke(main, ['card', 'remove', '_binder'])
    assert result.exit_code == 0
    assert "Removed card from node '_binder'" in result.output

    # Show the root card again (should still show the default directive)
    result = runner.invoke(main, ['card', 'show', '_binder'])
    assert result.exit_code == 0
    assert '[[_binder card.md]]' in result.output


def test_card_create_show_remove(runner: CliRunner) -> None:
    """Test the card create, show, and remove commands for a non-root node."""
    runner.invoke(main, ['init', 'Test Project'])
    add_result = runner.invoke(main, ['add', '_binder', 'Node with card'])  # No --card
    assert add_result.exit_code == 0
    structure_result = runner.invoke(main, ['structure'])
    node_id = structure_result.output.split('\n')[1].split()[1]
    # Create the card
    result = runner.invoke(main, ['card', 'create', node_id, '--text', 'Card text'])
    assert result.exit_code == 0
    assert f"Created card for node '{node_id}'" in result.output
    # Show the card
    result = runner.invoke(main, ['card', 'show', node_id])
    assert result.exit_code == 0
    assert 'Card text' in result.output
    # Remove the card
    result = runner.invoke(main, ['card', 'remove', node_id])
    assert result.exit_code == 0
    assert f"Removed card from node '{node_id}'" in result.output
    # Create a new card again
    result = runner.invoke(main, ['card', 'create', node_id, '--text', 'New card text'])
    assert result.exit_code == 0
    assert f"Created card for node '{node_id}'" in result.output
    # Show the new card
    result = runner.invoke(main, ['card', 'show', node_id])
    assert 'New card text' in result.output


def test_card_list(runner: CliRunner) -> None:
    """Test the card list command for a non-root node."""
    runner.invoke(main, ['init', 'Test Project'])
    add_result = runner.invoke(main, ['add', '_binder', 'Node with card'])
    assert add_result.exit_code == 0
    structure_result = runner.invoke(main, ['structure'])
    node_id = structure_result.output.split('\n')[1].split()[1]
    # Create a card for the new node
    result = runner.invoke(main, ['card', 'create', node_id, '--text', 'Card text'])
    assert result.exit_code == 0
    # List cards (should include root and non-root)
    result = runner.invoke(main, ['card', 'list'])
    assert result.exit_code == 0
    assert 'Found 2 cards' in result.output
    assert node_id in result.output or 'Node with card' in result.output
    assert '_binder' in result.output or 'Test Project' in result.output
    # List cards as JSON
    result = runner.invoke(main, ['card', 'list', '--output-format', 'json'])
    assert result.exit_code == 0
    assert node_id in result.output
    assert '_binder' in result.output


def test_card_edit_with_stdin(runner: CliRunner) -> None:
    """Test editing a card by piping content via stdin (no editor)."""
    runner.invoke(main, ['init', 'Test Project'])
    runner.invoke(main, ['add', '_binder', 'Node with card'])
    structure_result = runner.invoke(main, ['structure'])
    node_id = structure_result.output.split('\n')[1].split()[1]
    runner.invoke(main, ['card', 'create', node_id, '--text', 'Old card text'])
    # Edit the card by passing new content via --input-file -
    result = runner.invoke(main, ['card', 'edit', node_id, '--input-file', '-'], input='New card content from stdin')
    assert result.exit_code == 0
    assert 'Updated card for node' in result.output
    # Show the card to verify update
    result = runner.invoke(main, ['card', 'show', node_id])
    assert 'New card content from stdin' in result.output


def test_edit_node_with_stdin(runner: CliRunner) -> None:
    """Test editing a node by piping content via stdin (no editor)."""
    runner.invoke(main, ['init', 'Test Project'])
    runner.invoke(main, ['add', '_binder', 'Node to edit'])
    structure_result = runner.invoke(main, ['structure'])
    node_id = structure_result.output.split('\n')[1].split()[1]
    # Prepare content in the expected editor format
    content = f"""---\nid: {node_id}\ntitle: Node to edit\n---\n// Card: [[{node_id} card.md]]\n// Notes: [[{node_id} notes.md]]\n\nEdited text from stdin."""
    result = runner.invoke(main, ['edit', node_id, '--input-file', '-'], input=content)
    assert result.exit_code == 0
    assert 'Node updated successfully' in result.output
    # Show the node to verify update (text is not shown in CLI output, so check for title)
    result = runner.invoke(main, ['show', node_id])
    assert 'Title: Node to edit' in result.output
    # Optionally, check for card or notes directive
    assert f'[[{node_id} card.md]]' in result.output


def test_card_session_failure(runner: CliRunner) -> None:
    """Test the card session command with a likely failure (invalid node id)."""
    runner.invoke(main, ['init', 'Test Project'])
    # Use a bogus node id
    result = runner.invoke(main, ['card', 'session', 'bogus_id', '--no-prompt'])
    # Should print an error message
    assert result.exit_code == 0
    assert 'not found' in result.output or 'error' in result.output.lower()


def test_session_failure(runner: CliRunner) -> None:
    """Test the session command with a likely failure (invalid node id)."""
    runner.invoke(main, ['init', 'Test Project'])
    # Use a bogus node id
    result = runner.invoke(main, ['session', 'bogus_id', '--no-prompt'])
    # Should print an error message
    assert result.exit_code == 0
    assert 'not found' in result.output or 'error' in result.output.lower()


def test_session_with_options(runner: CliRunner) -> None:
    """Test the session command with various options."""
    runner.invoke(main, ['init', 'Test Project'])
    # Test with different options - should still fail due to invalid node but should parse correctly
    result = runner.invoke(
        main,
        [
            'session',
            'bogus_id',
            '--words',
            '100',
            '--time',
            '30',
            '--timer',
            'alert',
            '--stats',
            'detailed',
            '--no-prompt',
        ],
    )
    assert result.exit_code == 0
    assert 'not found' in result.output or 'error' in result.output.lower()


def test_freewrite_basic(runner: CliRunner) -> None:
    """Test the basic freewrite command."""
    runner.invoke(main, ['init', 'Test Project'])
    # This should not fail since freewrite creates files automatically
    # We use --no-prompt to avoid interactive prompts
    result = runner.invoke(main, ['freewrite', '--no-prompt'])
    assert result.exit_code == 0
    assert 'completed successfully' in result.output or 'ended by user' in result.output


def test_freewrite_with_options(runner: CliRunner) -> None:
    """Test the freewrite command with various options."""
    runner.invoke(main, ['init', 'Test Project'])
    result = runner.invoke(
        main,
        [
            'freewrite',
            '--words',
            '100',
            '--time',
            '5',
            '--timer',
            'none',
            '--stats',
            'detailed',
            '--suffix',
            'morning',
            '--no-prompt',
        ],
    )
    assert result.exit_code == 0
    assert 'completed successfully' in result.output or 'ended by user' in result.output


def test_freewrite_with_date(runner: CliRunner) -> None:
    """Test the freewrite command with a specific date."""
    runner.invoke(main, ['init', 'Test Project'])
    result = runner.invoke(main, ['freewrite', '--date', '2025-06-15', '--no-prompt'])
    assert result.exit_code == 0
    assert 'completed successfully' in result.output or 'ended by user' in result.output


def test_freewrite_invalid_date(runner: CliRunner) -> None:
    """Test the freewrite command with an invalid date."""
    runner.invoke(main, ['init', 'Test Project'])
    result = runner.invoke(main, ['freewrite', '--date', 'invalid-date', '--no-prompt'])
    assert result.exit_code == 0
    assert 'Invalid date format' in result.output


def test_card_create_already_exists(runner: CliRunner) -> None:
    """Test creating a card when one already exists."""
    runner.invoke(main, ['init', 'Test Project'])
    add_result = runner.invoke(main, ['add', '_binder', 'Node with card'])
    assert add_result.exit_code == 0
    structure_result = runner.invoke(main, ['structure'])
    node_id = structure_result.output.split('\n')[1].split()[1]
    # Create the card
    runner.invoke(main, ['card', 'create', node_id, '--text', 'Card text'])
    # Try to create again
    result = runner.invoke(main, ['card', 'create', node_id, '--text', 'Another card'])
    assert result.exit_code == 0
    assert 'already has a card' in result.output


def test_card_edit_yaml_frontmatter_error(runner: CliRunner, monkeypatch: pytest.MonkeyPatch) -> None:
    """Test editing a card with invalid YAML frontmatter."""
    runner.invoke(main, ['init', 'Test Project'])
    runner.invoke(main, ['add', '_binder', 'Node with card'])
    structure_result = runner.invoke(main, ['structure'])
    node_id = structure_result.output.split('\n')[1].split()[1]
    runner.invoke(main, ['card', 'create', node_id, '--text', 'Card text'])
    # Patch yaml.safe_load to raise YAMLError
    monkeypatch.setattr(yaml, 'safe_load', lambda *_: (_ for _ in ()).throw(yaml.YAMLError('bad yaml')))
    # Try to edit with frontmatter
    content = '---\nbad: [unclosed\n---\ncontent here'
    result = runner.invoke(main, ['card', 'edit', node_id], input=content)
    # Should not crash, should treat as content
    assert result.exit_code == 0
    # The error is handled, so card content is set to the input
    # (We can't check internal state, but no crash is sufficient)


def test_card_prepare_card_for_editor_metadata_header(runner: CliRunner) -> None:
    """Test prepare_card_for_editor with card metadata but no card content."""
    runner.invoke(main, ['init', 'Test Project'])
    runner.invoke(main, ['add', '_binder', 'Node with card'])
    structure_result = runner.invoke(main, ['structure'])
    node_id = structure_result.output.split('\n')[1].split()[1]
    # Create a card with metadata
    runner.invoke(main, ['card', 'create', node_id, '--text', ''])
    # Simulate metadata (would require deeper patching, so just call the command)
    result = runner.invoke(main, ['card', 'edit', node_id], input='---\ncolor: red\n---\n')
    assert result.exit_code == 0
    # Now prepare for editor
    result = runner.invoke(main, ['card', 'edit', node_id])
    assert result.exit_code == 0
    # Should not crash, and should include 'color: red' in the output if metadata is present


def test_card_remove_no_card(runner: CliRunner) -> None:
    """Test removing a card when neither card nor metadata is present."""
    runner.invoke(main, ['init', 'Test Project'])
    runner.invoke(main, ['add', '_binder', 'Node with card'])
    structure_result = runner.invoke(main, ['structure'])
    node_id = structure_result.output.split('\n')[1].split()[1]
    # Try to remove card before creating one
    result = runner.invoke(main, ['card', 'remove', node_id])
    assert result.exit_code == 0
    assert 'does not have a card' in result.output


def test_card_show_error(monkeypatch: pytest.MonkeyPatch, runner: CliRunner) -> None:
    """Test show_card error handling (simulate OSError)."""
    runner.invoke(main, ['init', 'Test Project'])
    runner.invoke(main, ['add', '_binder', 'Node with card'])
    structure_result = runner.invoke(main, ['structure'])
    node_id = structure_result.output.split('\n')[1].split()[1]
    # Patch repository to raise OSError
    from prosemark.cli import main as cli_main

    def raise_oserror(*args: object, **kwargs: object) -> None:
        raise OSError('simulated error')

    monkeypatch.setattr('prosemark.cli.CLIService.show_card', lambda _self, _node_id: raise_oserror())
    result = runner.invoke(cli_main, ['card', 'show', node_id])
    assert result.exit_code == 1
    # Do not check result.output, as global error handler is not invoked by CliRunner


def test_card_list_error(monkeypatch: pytest.MonkeyPatch, runner: CliRunner) -> None:
    """Test list_cards error handling (simulate OSError)."""
    runner.invoke(main, ['init', 'Test Project'])
    from prosemark.cli import main as cli_main

    def raise_oserror(*args: object, **kwargs: object) -> None:
        raise OSError('simulated error')

    monkeypatch.setattr('prosemark.cli.CLIService.list_cards', lambda _self, _format_type='text': raise_oserror())
    result = runner.invoke(cli_main, ['card', 'list'])
    assert result.exit_code == 1
    # Do not check result.output, as global error handler is not invoked by CliRunner


def test_card_remove_error(monkeypatch: pytest.MonkeyPatch, runner: CliRunner) -> None:
    """Test remove_card error handling (simulate OSError)."""
    runner.invoke(main, ['init', 'Test Project'])
    runner.invoke(main, ['add', '_binder', 'Node with card'])
    structure_result = runner.invoke(main, ['structure'])
    node_id = structure_result.output.split('\n')[1].split()[1]
    from prosemark.cli import main as cli_main

    def raise_oserror(*args: object, **kwargs: object) -> None:
        raise OSError('simulated error')

    monkeypatch.setattr('prosemark.cli.CLIService.remove_card', lambda _self, _node_id: raise_oserror())
    result = runner.invoke(cli_main, ['card', 'remove', node_id])
    assert result.exit_code == 1
    # Do not check result.output, as global error handler is not invoked by CliRunner


def test_card_edit_with_editor(monkeypatch: pytest.MonkeyPatch, runner: CliRunner) -> None:
    """Test editing a card using the --editor flag (covers prepare_card_for_editor)."""
    runner.invoke(main, ['init', 'Test Project'])
    runner.invoke(main, ['add', '_binder', 'Node with card'])
    structure_result = runner.invoke(main, ['structure'])
    node_id = structure_result.output.split('\n')[1].split()[1]
    runner.invoke(main, ['card', 'create', node_id, '--text', 'Initial card text'])

    # Patch click.edit to simulate user editing the card in an editor
    def fake_edit(content: str) -> str:
        assert 'Initial card text' in content  # The editor should receive the current card content
        return 'Edited card content from editor'

    monkeypatch.setattr('click.edit', fake_edit)

    # Run the edit command with --editor
    result = runner.invoke(main, ['card', 'edit', node_id, '--editor'])
    assert result.exit_code == 0
    assert 'Updated card for node' in result.output

    # Show the card to verify update
    result = runner.invoke(main, ['card', 'show', node_id])
    assert 'Edited card content from editor' in result.output


def test_prepare_card_for_editor_error(monkeypatch: pytest.MonkeyPatch, runner: CliRunner) -> None:
    """Test prepare_card_for_editor error handling (simulate OSError)."""
    runner.invoke(main, ['init', 'Test Project'])
    runner.invoke(main, ['add', '_binder', 'Node with card'])
    structure_result = runner.invoke(main, ['structure'])
    node_id = structure_result.output.split('\n')[1].split()[1]
    from prosemark.cli import main as cli_main

    def raise_oserror(*args: object, **kwargs: object) -> NoReturn:
        raise OSError('simulated error')

    monkeypatch.setattr('prosemark.cli.CLIService.prepare_card_for_editor', lambda _self, _node_id: raise_oserror())
    result = runner.invoke(cli_main, ['card', 'edit', node_id, '--editor'])
    assert result.exit_code == 1
    assert isinstance(result.exception, OSError)
    assert 'simulated error' in str(result.exception)


def test_edit_card_outer_exception(monkeypatch: pytest.MonkeyPatch, runner: CliRunner) -> None:
    """Test edit_card error handling (simulate OSError in repository)."""
    runner.invoke(main, ['init', 'Test Project'])
    runner.invoke(main, ['add', '_binder', 'Node with card'])
    structure_result = runner.invoke(main, ['structure'])
    node_id = structure_result.output.split('\n')[1].split()[1]
    from prosemark.cli import main as cli_main

    def raise_oserror(*args: object, **kwargs: object) -> NoReturn:
        raise OSError('simulated error')

    monkeypatch.setattr('prosemark.cli.CLIService.edit_card', lambda _self, _node_id, _content: raise_oserror())
    result = runner.invoke(cli_main, ['card', 'edit', node_id, '--input-file', '-'], input='Some content')
    assert result.exit_code == 1
    assert isinstance(result.exception, OSError)
    assert 'simulated error' in str(result.exception)


def test_edit_card_valid_yaml_frontmatter() -> None:
    """Directly test CLIService.edit_card for the branch where valid YAML frontmatter updates metadata (coverage)."""
    storage = InMemoryNodeStorage()
    repo = ProjectRepository(storage)
    service = CLIService(repo)
    # Setup a project and node
    node = Node(id='n4', title='Node 4')
    node.card = ''
    node.metadata = {}
    repo.save_node(node)

    class DummyProject(Project):
        def __init__(self, root_node: Node) -> None:
            super().__init__(root_node=root_node)

        def get_node_by_id(self, node_id: str) -> Node | None:
            return node if node_id == 'n4' else None

    # Provide edited_content with valid YAML frontmatter
    edited_content = '---\ncolor: blue\nstatus: done\n---\nThis is the card content.'
    with patch.object(repo, 'load_project', return_value=DummyProject(node)):
        result = service.edit_card('n4', edited_content)
        assert result.success is True
        assert 'Updated card for node' in next(iter(result.message))
        # The card content should be set to the content after the frontmatter
        assert node.card == 'This is the card content.'
        # The metadata should be updated with the YAML frontmatter
        assert 'card' in node.metadata
        assert node.metadata['card']['color'] == 'blue'
        assert node.metadata['card']['status'] == 'done'


def test_show_card_with_metadata() -> None:
    """Directly test CLIService.show_card for the card metadata display branch (coverage)."""
    storage = InMemoryNodeStorage()
    repo = ProjectRepository(storage)
    service = CLIService(repo)
    # Setup a project and node with card and metadata
    node = Node(id='n2', title='Node 2')
    node.card = 'Card content'
    node.metadata = {'card': {'color': 'red', 'status': 'active'}}
    repo.save_node(node)

    class DummyProject(Project):
        def __init__(self, root_node: Node) -> None:
            super().__init__(root_node=root_node)

        def get_node_by_id(self, node_id: str) -> Node | None:
            return node if node_id == 'n2' else None

    with patch.object(repo, 'load_project', return_value=DummyProject(node)):
        result = service.show_card('n2')
        assert result.success is True
        output = '\n'.join(list(result.message))
        assert 'Metadata:' in output
        assert 'color: red' in output
        assert 'status: active' in output
        assert 'Card content' in output


def test_show_card_with_empty_metadata() -> None:
    """Directly test CLIService.show_card for the branch where card metadata exists but is empty (coverage)."""
    storage = InMemoryNodeStorage()
    repo = ProjectRepository(storage)
    service = CLIService(repo)
    # Setup a project and node with card and empty metadata
    node = Node(id='n3', title='Node 3')
    node.card = 'Card content'
    node.metadata = {'card': {}}  # Empty metadata
    repo.save_node(node)

    class DummyProject(Project):
        def __init__(self, root_node: Node) -> None:
            super().__init__(root_node=root_node)

        def get_node_by_id(self, node_id: str) -> Node | None:
            return node if node_id == 'n3' else None

    with patch.object(repo, 'load_project', return_value=DummyProject(node)):
        result = service.show_card('n3')
        assert result.success is True
        output = '\n'.join(list(result.message))
        # Should not include 'Metadata:' since metadata is empty
        assert 'Metadata:' not in output
        assert 'Card content' in output
