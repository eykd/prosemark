"""CLI layer - Command-line interface implementation.

This package contains the command-line interface for the prosemark application,
providing user interaction capabilities through terminal commands.
The CLI acts as an adapter that translates user commands into application use cases.
"""

# Import all command functions for external use
from prosemark.cli.add import add_command
from prosemark.cli.audit import audit_command
from prosemark.cli.edit import edit_command
from prosemark.cli.init import init_command
from prosemark.cli.main import main
from prosemark.cli.materialize import materialize_command
from prosemark.cli.move import move_command
from prosemark.cli.remove import remove_command
from prosemark.cli.structure import structure_command
from prosemark.cli.write import write_command

__all__ = [
    'add_command',
    'audit_command',
    'edit_command',
    'init_command',
    'main',
    'materialize_command',
    'move_command',
    'remove_command',
    'structure_command',
    'write_command',
]
