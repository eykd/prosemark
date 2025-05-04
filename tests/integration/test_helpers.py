import re
from pathlib import Path
from typing import Any

from prosemark.domain.nodes import Node
from prosemark.domain.projects import Project


def get_project_structure(project: Project) -> dict[str, Any]:
    """Get a dictionary representation of the project structure.
    
    Args:
        project: The project to analyze.
        
    Returns:
        A dictionary representing the project structure.

    """
    result = {
        'name': project.name,
        'description': project.description,
        'nodes': {}
    }

    if project.root_node:
        result['nodes'] = _build_node_structure(project.root_node)

    return result


def _build_node_structure(node: Node) -> dict[str, Any]:
    """Recursively build a dictionary representation of a node and its children.
    
    Args:
        node: The node to analyze.
        
    Returns:
        A dictionary representing the node structure.

    """
    result = {
        'id': node.node_id,
        'title': node.title,
        'notecard': node.notecard,
        'content': node.content,
        'notes': node.notes,
        'children': {}
    }

    for child in node.children:
        result['children'][child.node_id] = _build_node_structure(child)

    return result


def verify_file_structure(project_dir: Path, expected_files: list[str]) -> bool:
    """Verify that the project directory contains the expected files.
    
    Args:
        project_dir: The project directory to check.
        expected_files: A list of expected file names.
        
    Returns:
        True if all expected files exist, False otherwise.

    """
    for file_name in expected_files:
        file_path = project_dir / file_name
        if not file_path.exists():
            return False

    return True


def count_markdown_files(directory: Path) -> int:
    """Count the number of Markdown files in a directory.
    
    Args:
        directory: The directory to check.
        
    Returns:
        The number of Markdown files found.

    """
    return len(list(directory.glob('*.md')))


def extract_node_ids_from_markdown(markdown_content: str) -> list[str]:
    """Extract node IDs from Markdown content.
    
    Args:
        markdown_content: The Markdown content to parse.
        
    Returns:
        A list of node IDs found in the content.

    """
    # Look for links in the format [title](node_id.md)
    pattern = r'\[.*?\]\(([^)]+)\.md\)'
    matches = re.findall(pattern, markdown_content)

    # Remove .md extension if present
    return [match.replace('.md', '') for match in matches]
