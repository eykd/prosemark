# Prosemark October MVP — Unified Hexagonal Architecture Specification

## 1. Scope & Purpose

The October MVP delivers a **CLI-based writing tool** with the following core features:

- **Binder-as-title**: `_binder.md` is the canonical project outline and hierarchy.
- **Node triplet**: Each node consists of:
  - Draft (`{id}.md` with YAML frontmatter)
  - Notes (`{id}.notes.md`)
  - Synopsis (stored in frontmatter of `{id}.md`)
- **Daily freewrites**: Timestamped files outside the binder for frictionless writing.

> Non-goals for October: session tracking, analytics, tagging, AI helpers, compilation, community features. These belong to later phases.

The design follows **Hexagonal Architecture (Ports & Adapters)** for future extensibility to GUI or web without altering the domain.

---

## 2. Architectural Goals & Constraints

- **Hexagonal (ports & adapters)**: Pure domain logic; all I/O is isolated.
- **Plain text first**: Markdown + YAML. Files Obsidian-compatible.
- **Stability**: Identity = UUIDv7, exposed in filenames and binder links.
- **Resilience**: Binder allows arbitrary free-form prose outside managed block.
- **Determinism & testability**: Pure functions where possible; side effects behind ports.
- **CLI-first**: Simple commands that map directly to use-cases.

---

## 3. Domain Layer

### Core Entities

- **Node**
  - `id: NodeId` (UUIDv7, immutable)
  - `title: str | None`
  - `synopsis: str | None`
  - `body: MarkdownText`
  - `notes: MarkdownText`

- **Binder**
  - `roots: List[BinderItem]`
  - Hierarchical, ordered structure.

- **BinderItem**
  - `id: Optional[NodeId]` (None = placeholder)
  - `display_title: str`
  - `children: List[BinderItem]`

- **Freewrite**
  - Timestamped note not included in binder.

### Value Objects

- `NodeId`: Stable identity, must match filename and frontmatter.
- `NodeMetadata`: Frontmatter subset `{id, title, synopsis, created, updated}`.
- `BinderTree`: Immutable snapshot of `_binder.md` managed block.
- `Timestamp`: UTC ISO8601 string.

### Invariants

- `frontmatter.id` == filename id.
- Binder must not contain duplicate IDs.
- Placeholders allowed (empty href in binder).
- Orphaned files possible but detected by `audit`.

---

## 4. Application Layer (Use Cases)

- `InitProject`
- `AddNode`
- `MoveNode`
- `RemoveNode`
- `EditPart` (draft, notes, synopsis)
- `ShowPart`
- `ShowStructure`
- `WriteFreeform`
- `MaterializeNode` (fill in placeholders, create missing files)
- `AuditBinder` (report inconsistencies)

Each use case is a pure orchestrator: interacts only with domain entities and ports.

---

## 5. Ports (Interfaces)

```python
class BinderRepo(Protocol):
    def load(self) -> Binder: ...
    def save(self, binder: Binder) -> None: ...

class NodeRepo(Protocol):
    def create(self, id: NodeId, title: str | None, synopsis: str | None) -> None: ...
    def read_frontmatter(self, id: NodeId) -> dict: ...
    def write_frontmatter(self, id: NodeId, fm: dict) -> None: ...
    def open_in_editor(self, id: NodeId, part: str) -> None: ...
    def delete(self, id: NodeId, *, delete_files: bool) -> None: ...

class DailyRepo(Protocol):
    def write_freeform(self, title: str | None) -> str: ...

class IdGenerator(Protocol):
    def new(self) -> NodeId: ...

class Clock(Protocol):
    def now_iso(self) -> str: ...

class Logger(Protocol):
    def info(self, msg: str): ...
    def warn(self, msg: str): ...
    def error(self, msg: str): ...

class EditorPort(Protocol):
    def open(self, path: str, *, cursor_hint: str | None = None): ...

class ConsolePort(Protocol):
    def print(self, msg: str): ...
```

---

## 6. Adapters

### Inbound
- **CLI Adapter**: `pmk` → maps commands to use cases.

### Outbound
- **BinderRepoFs**: Reads/writes `_binder.md`, preserves text outside markers.
- **NodeRepoFs**: Manages `{id}.md` and `{id}.notes.md`, validates IDs.
- **DailyRepoFs**: Creates timestamped freewrites.
- **EditorLauncher**: Resolves `$EDITOR` or OS default.
- **IdGeneratorUuid7**: Generates sortable UUIDv7.
- **ClockSystem**: UTC ISO timestamps.
- **ConsolePretty**: Formats and prints structure trees.

---

## 7. File Design

### Binder (`_binder.md`)

```markdown
# Binder

Notes can go here.

## Binder (managed by Prosemark)
<!-- pmk:begin-binder -->
- [Chapter 1 – Mercy Run](0192f0c1.md)
- [New Placeholder]()
<!-- pmk:end-binder -->
```

- Only fenced block is managed.
- Placeholder = empty href.

### Node (`{id}.md`)

```yaml
---
id: 0192f0c1
title: "Chapter 1 – Mercy Run"
synopsis: |
  Free-form synopsis text…
created: 2025-09-10T10:00:00-07:00
updated: 2025-09-10T10:00:00-07:00
---
```

Body follows.

### Notes (`{id}.notes.md`)
- Optional, free-form Markdown.

### Freewrite
- Filename: `YYYYMMDDTHHMM_<uuid7>.md`
- Frontmatter includes optional title, id, created.

---

## 8. Commands (CLI)

- `pmk init`
- `pmk add --parent <ID|ROOT> --synopsis "…" --edit "<Title>"`
- `pmk move <ID> --parent <NEW_PARENT> [--position N]`
- `pmk remove <ID> [--delete-files]`
- `pmk edit <ID> --part draft|notes|synopsis`
- `pmk show <ID> --part draft|notes|synopsis`
- `pmk structure [--node <ID>]`
- `pmk write ["optional title"]`
- `pmk materialize <PLACEHOLDER>`
- `pmk audit`

---

## 9. Audit Rules

- **PLACEHOLDER**: No ID in binder.
- **MISSING**: Binder references file that doesn’t exist.
- **ORPHAN**: File exists but not in binder.
- **MISMATCH**: Frontmatter id ≠ filename.

Output: human-readable tree or JSON.

---

## 10. Error Model

- `BinderIntegrityError`
- `NodeIdentityError`
- `BinderNotFoundError`
- `NodeNotFoundError`
- `FilesystemError`

Application layer maps to CLI exit codes and friendly messages.

---

## 11. Configuration

`.prosemark.yml`:

```yaml
editor: "$EDITOR"
daily_prefix: "%Y%m%dT%H%M"
binder_file: "_binder.md"
managed_header: "## Binder (managed by Prosemark)"
begin_marker: "<!-- pmk:begin-binder -->"
end_marker:   "<!-- pmk:end-binder -->"
notes_suffix: ".notes.md"
```

Overrides allowed by env vars and CLI flags.

---

## 12. Packaging & Project Layout

```
prosemark/
  domain/
    models.py
    policies.py
  app/
    use_cases.py
  ports/
    binder_repo.py
    node_repo.py
    daily_repo.py
    system.py
  adapters/
    fs_binder_repo.py
    fs_node_repo.py
    fs_daily_repo.py
    frontmatter_codec.py
    md_binder_parser.py
    system_uuid7.py
    system_clock.py
    editor_launcher.py
  cli/
    main.py
  tests/
    unit/
    contract/
    golden/
pyproject.toml
uv.lock
```

---

## 13. Testing Strategy

- **Contract tests**: Adapters vs port contracts.
- **Golden-file tests**: Binder parsing round-trips with noisy input.
- **Property-based tests**: Binder tree invariants.
- **CLI integration tests**: Simulate workflows (`add`, `move`, `remove`).

---

## 14. Observability & DX

- Structured logging (action, id, duration).
- `--dry-run` flag for binder mutations.
- `pmk audit` for diagnostics.

---

## 15. Future Extensions

- **Sessions & stats**: Word count, streak tracking.
- **GUI adapters**: Tauri/Electron or Qt.
- **Web backend**: DB-backed repos via HTTP ports.
- **Git hooks**: Automatic commits.
- **Search/Tags**: Indexing service.

---

## 16. Acceptance Criteria (MVP)

- Binder round-trip preserves non-managed text byte-for-byte.
- Nodes created with valid frontmatter.
- Placeholders supported and materializable.
- Freewrites created with timestamp + UUID.
- CLI commands map directly to use cases.
- `audit` reports inconsistencies correctly.
