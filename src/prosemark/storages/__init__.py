"""Storage adapters for prosemark"""

from prosemark.storages.base import NodeStoragePort
from prosemark.storages.filesystem import FilesystemMdNodeStorage

__all__ = ['FilesystemMdNodeStorage', 'NodeStoragePort']
