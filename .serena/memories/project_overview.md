# Prosemark Project Overview

## Purpose
Prosemark is a command-line tool for planning, organizing, and writing stories using a hierarchical document structure. It follows hexagonal architecture principles with clear separation between domain logic, application services, and external adapters.

## Tech Stack
- Python 3.13+
- Click for CLI framework
- Pydantic for data validation
- PyYAML for configuration
- UUID-Extension for NodeId generation
- Pytest for testing
- Ruff for linting and formatting
- MyPy for type checking

## Architecture
- **Domain Layer**: Core business models and policies (`src/prosemark/domain/`)
- **Application Layer**: Use case interactors (`src/prosemark/app/`)
- **Ports**: Abstract interfaces for external dependencies (`src/prosemark/ports/`)
- **Adapters**: Concrete implementations of ports (`src/prosemark/adapters/`)
- **CLI**: Command-line interface (`src/prosemark/cli/`)

## Key Concepts
- **Binder**: Hierarchical structure of nodes stored in `_binder.md`
- **Node**: Individual content units with `.md` and `.notes.md` files
- **NodeId**: UUIDv7 identifiers for unique node identification
- **BinderItem**: Hierarchical structure elements with display titles and children
