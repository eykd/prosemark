"""Factories for creating domain objects"""

from polyfactory import Use
from polyfactory.factories.dataclass_factory import DataclassFactory

from prosemark.domain.nodes import Node
from prosemark.domain.projects import Project


class NodeFactory(DataclassFactory[Node]):
    """Factory for creating Node objects"""

    __model__ = Node

    id = Use(Node.generate_id)
    title = ''
    card = ''
    text = ''
    notes = ''
    metadata: dict[str, str] = Use(dict)  # type: ignore[assignment]
    parent = None
    children: list[Node] = Use(list)  # type: ignore[assignment]


class RootNodeFactory(NodeFactory):
    """Factory for creating root Node objects"""

    id = '_binder'  # type: ignore[assignment]
    title = 'New Project'


class ProjectFactory(DataclassFactory[Project]):
    """Factory for creating Project objects"""

    __model__ = Project

    root_node = Use(RootNodeFactory.build)
