# Textual TUI Framework Research

## Framework Overview

**Decision**: Use Textual as the TUI framework for Python-based terminal applications
**Rationale**: Textual is a mature, feature-rich Python Rapid Application Development (RAD) framework specifically designed for sophisticated terminal user interfaces. It offers:
- Native Python development with familiar patterns
- Cross-platform compatibility and SSH support
- Rich widget library and flexible layout system
- Event-driven architecture with reactive programming
- MIT licensed and actively maintained
- Excellent documentation and examples

**Alternatives considered**:
- Rich (same author, but focused on terminal output rather than interactive apps)
- urwid (older, more complex API)
- py-cui (less mature, smaller community)
- Custom ncurses wrapper (high complexity, low-level)

## 1. Creating a TUI Application with Textual

**Decision**: Use App class inheritance pattern with compose() method for widget management
**Rationale**: This is the standard Textual pattern that provides clean separation of concerns and follows object-oriented design principles.

```python
from textual.app import App
from textual.widgets import Static, Input
from textual.containers import VerticalScroll

class MyTUIApp(App):
    """A Textual app for freewriting."""

    CSS = """
    Screen {
        layout: vertical;
    }

    #content {
        height: 80%;
        border: solid $primary;
    }

    #input_container {
        height: 20%;
        border: solid $secondary;
    }
    """

    def compose(self):
        """Create child widgets for the app."""
        yield VerticalScroll(id="content")
        yield Input(placeholder="Enter your thoughts...", id="input_box")

    def on_mount(self):
        """Called when app starts."""
        self.title = "Freewriting Tool"
        self.sub_title = "Write freely without interruption"

if __name__ == "__main__":
    app = MyTUIApp()
    app.run()
```

**Alternatives considered**:
- Functional approach (not supported by Textual's design)
- Multiple inheritance patterns (adds complexity)

## 2. Creating Split Layout (80% Content, 20% Input)

**Decision**: Use CSS-based vertical layout with percentage heights
**Rationale**: Textual's CSS system provides precise control over widget sizing and is more maintainable than programmatic layout management.

```python
CSS = """
Screen {
    layout: vertical;
}

#content_area {
    height: 80%;
    border: solid $primary;
    padding: 1;
}

#input_container {
    height: 20%;
    border: solid $secondary;
    padding: 1;
}

#input_box {
    width: 100%;
}
"""

def compose(self):
    with VerticalScroll(id="content_area"):
        yield Static("", id="content_display")
    with Container(id="input_container"):
        yield Input(placeholder="Type here and press Enter...", id="input_box")
```

**Alternatives considered**:
- Grid layout (more complex for simple split)
- Horizontal layout (doesn't match requirement)
- Dock layout (less flexible for proportional sizing)
- Programmatic sizing with reactive attributes (less declarative)

## 3. Handling Text Input with Readline-Style Editing

**Decision**: Use Textual's Input widget which provides built-in readline functionality
**Rationale**: The Input widget includes comprehensive text editing features without additional dependencies:

```python
from textual.widgets import Input

class FreewritingInput(Input):
    """Enhanced input with custom behavior."""

    def __init__(self, **kwargs):
        super().__init__(
            placeholder="Start writing...",
            **kwargs
        )

    # Readline features available by default:
    # - Ctrl+A: beginning of line
    # - Ctrl+E: end of line
    # - Ctrl+K: kill to end of line
    # - Ctrl+U: kill to beginning of line
    # - Arrow keys: navigate
    # - Ctrl+D: delete character
    # - Backspace: delete previous character
```

**Alternatives considered**:
- TextArea widget (overkill for single-line input, though supports multi-line)
- Custom input widget from scratch (reinventing the wheel)
- External readline library integration (adds complexity)

## 4. Real-Time Display Updates

**Decision**: Use reactive attributes and watch methods for real-time updates
**Rationale**: Textual's reactive system automatically handles UI updates when data changes, providing smooth real-time behavior.

```python
from textual.reactive import reactive
from textual.widgets import Static
from textual.containers import VerticalScroll

class ContentDisplay(Static):
    """Widget to display accumulated content."""

    content_text = reactive("")

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def watch_content_text(self, text: str) -> None:
        """Called automatically when content_text changes."""
        self.update(text)

class FreewritingApp(App):
    content = reactive("")

    def compose(self):
        yield VerticalScroll(ContentDisplay(), id="content_area")
        yield Input(id="input_box")

    def add_content(self, new_text: str):
        """Add new content and trigger UI update."""
        self.content += new_text + "\n"
        self.query_one(ContentDisplay).content_text = self.content
```

**Alternatives considered**:
- Manual UI updates with update() calls (error-prone)
- Timer-based polling (inefficient)
- External state management (adds complexity)

## 5. Event Handling for ENTER Key

**Decision**: Use Input.Submitted event handler with message system
**Rationale**: This is the idiomatic Textual pattern for handling form submission and provides clean event propagation.

```python
from textual.widgets import Input

class FreewritingApp(App):
    def compose(self):
        yield VerticalScroll(id="content_area")
        yield Input(id="input_box")

    def on_input_submitted(self, event: Input.Submitted) -> None:
        """Handle ENTER key press in input box."""
        input_widget = event.input
        text = input_widget.value

        if text.strip():  # Only process non-empty input
            self.add_to_content(text)
            input_widget.clear()  # Clear input for next entry

    def add_to_content(self, text: str):
        """Add text to the main content area."""
        content_area = self.query_one("#content_area")
        content_area.mount(Static(text))
```

**Alternative approach using custom key handler**:
```python
def on_key(self, event) -> None:
    """Alternative: handle key events directly."""
    if event.key == "enter":
        input_widget = self.query_one("#input_box")
        if input_widget.has_focus:
            # Process input...
            pass
```

**Alternatives considered**:
- Raw key event handling (less specific, more complex)
- Custom message types (unnecessary for standard input submission)
- Polling input value (inefficient and non-reactive)

## 6. Best Practices for Textual App Structure

**Decision**: Follow MVC-like separation with App as controller, custom widgets as views, and reactive data as model
**Rationale**: This pattern scales well and maintains code organization as applications grow in complexity.

```python
# Recommended structure:
freewriting_app/
├── __init__.py
├── app.py              # Main App class
├── widgets/
│   ├── __init__.py
│   ├── content_display.py    # Content viewing widget
│   ├── input_box.py          # Enhanced input widget
│   └── status_bar.py         # Status information
├── styles/
│   └── app.css         # External CSS file
└── models/
    └── content.py      # Data models and business logic

# app.py
class FreewritingApp(App):
    CSS_PATH = "styles/app.css"
    TITLE = "Freewriting Tool"

    def __init__(self):
        super().__init__()
        self.content_model = ContentModel()

    def compose(self):
        yield Header()
        yield ContentDisplay(self.content_model)
        yield InputBox()
        yield Footer()

    # Event handlers coordinate between widgets
    def on_input_submitted(self, event):
        self.content_model.add_entry(event.value)
```

**Alternatives considered**:
- Single-file applications (doesn't scale)
- Functional composition (not well-supported by Textual)
- Complex inheritance hierarchies (harder to maintain)

## 7. Integration with Existing Typer CLI Commands

**Decision**: Create a hybrid approach where Typer handles CLI argument parsing and Textual provides the interactive interface
**Rationale**: This leverages the strengths of both frameworks while maintaining compatibility with existing CLI infrastructure and providing excellent type safety.

```python
import typer
from textual.app import App
from typing import Optional

class FreewritingApp(App):
    def __init__(self, config, **kwargs):
        super().__init__(**kwargs)
        self.config = config  # Configuration from Typer

def freewrite(
    node: Optional[str] = typer.Argument(None, help="Target node UUID"),
    title: Optional[str] = typer.Option(None, "--title", help="Optional title"),
    theme: str = typer.Option("dark", help="UI theme"),
    autosave: int = typer.Option(300, help="Autosave interval in seconds"),
    output: Optional[str] = typer.Option(None, "-o", help="Output file path")
):
    """Start the freewriting TUI interface."""
    config = {
        'node': node,
        'title': title,
        'theme': theme,
        'autosave_interval': autosave,
        'output_file': output
    }

    app = FreewritingApp(config)
    app.run()

# Integration pattern:
app = typer.Typer()

@app.command()
def batch_mode(filename: str):
    """Process file in batch mode."""
    # Existing CLI functionality
    pass

@app.command()
def write(
    node: Optional[str] = None,
    title: Optional[str] = typer.Option(None, "--title"),
    theme: str = typer.Option("dark")
):
    """Start interactive TUI mode."""
    config = {'node': node, 'title': title, 'theme': theme}
    app_instance = FreewritingApp(config)
    app_instance.run()

if __name__ == "__main__":
    app()
```

**Alternative patterns**:
```python
# Pattern 1: TUI as Typer command
app = typer.Typer()

@app.command()
def tui():
    """Start TUI interface."""
    FreewritingApp().run()

# Pattern 2: Conditional TUI launch
def main(
    tui: bool = typer.Option(False, "--tui", help="Start TUI interface"),
    input_file: Optional[str] = typer.Argument(None)
):
    if tui:
        FreewritingApp().run()
    else:
        # CLI mode
        process_file(input_file)
```

**Alternatives considered**:
- Replace Typer entirely with Textual (loses CLI compatibility and type safety)
- Separate applications (duplicated configuration and logic)
- Textual-only with custom argument parsing (reinventing Typer's functionality)

## Additional Code Examples

### Complete Minimal Freewriting App
```python
from textual.app import App
from textual.widgets import Static, Input, Header, Footer
from textual.containers import VerticalScroll, Container
from textual.reactive import reactive

class FreewritingApp(App):
    """A simple freewriting TUI application."""

    CSS = """
    #content_area {
        height: 80%;
        border: solid $primary;
        padding: 1;
    }

    #input_container {
        height: 20%;
        border: solid $secondary;
        padding: 1;
    }

    .entry {
        margin-bottom: 1;
        padding: 1;
        background: $surface;
    }
    """

    entry_count = reactive(0)

    def compose(self):
        yield Header()
        yield VerticalScroll(id="content_area")
        with Container(id="input_container"):
            yield Input(
                placeholder="Start writing... (Press Enter to add entry)",
                id="input_box"
            )
        yield Footer()

    def on_input_submitted(self, event: Input.Submitted) -> None:
        """Handle new text input."""
        text = event.value.strip()
        if text:
            self.add_entry(text)
            event.input.clear()

    def add_entry(self, text: str) -> None:
        """Add a new text entry to the content area."""
        self.entry_count += 1
        content_area = self.query_one("#content_area")

        entry = Static(
            f"[{self.entry_count:03d}] {text}",
            classes="entry"
        )
        content_area.mount(entry)
        content_area.scroll_end()  # Auto-scroll to bottom

    def on_mount(self) -> None:
        """Initialize the application."""
        self.title = "Freewriting Tool"
        self.sub_title = "Write freely without interruption"

        # Focus the input box
        self.query_one("#input_box").focus()

if __name__ == "__main__":
    FreewritingApp().run()
```

### Advanced Features Integration
```python
from datetime import datetime
from pathlib import Path
import json

class AdvancedFreewritingApp(App):
    """Enhanced freewriting app with persistence and stats."""

    def __init__(self, config=None, **kwargs):
        super().__init__(**kwargs)
        self.config = config or {}
        self.entries = []
        self.start_time = datetime.now()

    def on_mount(self):
        """Setup app with configuration."""
        if self.config.get('autosave_interval'):
            self.set_interval(
                self.config['autosave_interval'],
                self.autosave
            )

    def add_entry(self, text: str):
        """Enhanced entry addition with metadata."""
        entry_data = {
            'text': text,
            'timestamp': datetime.now().isoformat(),
            'word_count': len(text.split())
        }
        self.entries.append(entry_data)

        # Update UI
        content_area = self.query_one("#content_area")
        formatted_entry = self.format_entry(entry_data)
        content_area.mount(Static(formatted_entry))

        # Update stats
        self.update_stats()

    def format_entry(self, entry_data: dict) -> str:
        """Format entry for display."""
        time_str = datetime.fromisoformat(entry_data['timestamp']).strftime("%H:%M")
        return f"[{time_str}] {entry_data['text']} ({entry_data['word_count']} words)"

    def autosave(self):
        """Automatically save entries."""
        if self.config.get('output_file') and self.entries:
            self.save_to_file(Path(self.config['output_file']))

    def save_to_file(self, filepath: Path):
        """Save entries to JSON file."""
        with filepath.open('w') as f:
            json.dump({
                'entries': self.entries,
                'session_start': self.start_time.isoformat(),
                'total_entries': len(self.entries),
                'total_words': sum(e['word_count'] for e in self.entries)
            }, f, indent=2)
```

## Conclusion

Textual provides an excellent foundation for building sophisticated terminal user interfaces in Python. Its reactive system, comprehensive widget library, and CSS-based styling make it ideal for the freewriting application requirements. The framework's design patterns align well with Python best practices and integrate smoothly with existing CLI tools like Typer.

The recommended approach uses Textual's built-in capabilities for layout management, input handling, and real-time updates while maintaining clean separation of concerns through proper application structure. This approach will create a responsive, professional TUI application that meets all specified requirements.
