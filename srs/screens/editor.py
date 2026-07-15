"""Embedded note editor — allow text modification directly inside TUI."""

from __future__ import annotations

from pathlib import Path

from textual.app import ComposeResult
from textual.containers import Vertical
from textual.screen import Screen
from textual.widgets import Static, TextArea


class EditorScreen(Screen[bool]):
    """Inline markdown editor using TextArea."""

    CSS = """
    EditorScreen {
        padding: 1 2;
    }
    #editor-title {
        text-style: bold;
        color: $foreground;
        padding: 0 1;
        margin-bottom: 1;
        width: 100%;
        border-bottom: solid $primary;
    }
    #editor-textarea {
        height: 1fr;
        border: round $panel;
    }
    #editor-textarea:focus {
        border: double $accent;
    }
    #editor-footer {
        color: $text-muted;
        margin-top: 1;
        text-align: center;
    }
    """

    BINDINGS = [
        ("ctrl+s", "save_note", "Save"),
        ("escape", "cancel", "Cancel"),
    ]

    def __init__(self, filepath: Path) -> None:
        super().__init__()
        self.filepath = filepath

    def compose(self) -> ComposeResult:
        try:
            content = self.filepath.read_text(encoding="utf-8") if self.filepath.exists() else ""
        except Exception:
            content = ""

        with Vertical():
            yield Static(f"Editing: {self.filepath.name}", id="editor-title")
            yield TextArea(content, language="markdown", id="editor-textarea")
            yield Static("ctrl+s: save and exit  Esc: cancel", id="editor-footer")

    def on_mount(self) -> None:
        self.query_one("#editor-textarea", TextArea).focus()

    def action_save_note(self) -> None:
        text = self.query_one("#editor-textarea", TextArea).text
        try:
            self.filepath.parent.mkdir(parents=True, exist_ok=True)
            self.filepath.write_text(text, encoding="utf-8")
            self.notify("File saved successfully")
            self.dismiss(True)
        except Exception as e:
            self.notify(f"Save failed: {e}", severity="error")

    def action_cancel(self) -> None:
        self.dismiss(False)
