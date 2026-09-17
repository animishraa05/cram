"""Help screen — keyboard shortcut cheatsheet, press ? to open."""

from __future__ import annotations

from textual.app import ComposeResult
from textual.containers import Vertical
from textual.screen import Screen
from textual.widgets import DataTable, Static


_BINDINGS_TABLE: list[tuple[str, str, str]] = [
    ("j / k",       "Anywhere",        "Move cursor down / up"),
    ("o / Enter",   "Anywhere",        "Select / confirm"),
    ("Esc",         "Anywhere",        "Go back / cancel"),
    ("q",           "Home",            "Quit (with confirm dialog)"),
    ("?",           "Anywhere",        "Show this help"),
    (",",           "Anywhere",        "Open Settings"),
    ("/",           "Browse",          "Focus search box"),
    ("n",           "Review",          "Skip selected card"),
    ("d",           "Browse",          "Delete selected card"),
    ("e",           "Browse",          "Edit topic of selected card"),
    ("a/h/g/e",     "Rating dialog",   "Rate: Again / Hard / Good / Easy"),
    ("← →",         "Rating dialog",   "Move focus between rating buttons"),
    ("Ctrl+s",      "Settings",        "Save settings"),
    ("Ctrl+h/l",    "Settings",        "Focus config / theme column"),
]


class HelpScreen(Screen):
    """Full-screen keyboard shortcut cheatsheet."""

    BINDINGS = [
        ("escape", "dismiss_help", "Close"),
        ("question_mark", "dismiss_help", "Close"),
    ]

    CSS = """
    HelpScreen {
        align: center middle;
        background: $background 80%;
    }
    #help-container {
        width: 80;
        max-width: 95%;
        height: auto;
        max-height: 90%;
        background: $surface;
        border: round $panel;
        padding: 1 2;
    }
    #help-title {
        text-style: bold;
        color: $foreground;
        padding: 0 1;
        margin-bottom: 1;
        width: 100%;
        content-align-horizontal: center;
        border-bottom: solid $primary;
    }
    #help-table {
        height: auto;
        width: 100%;
        margin-bottom: 1;
    }
    #help-footer {
        color: $text-muted;
        width: 100%;
        content-align-horizontal: center;
        border-top: solid $panel;
        padding-top: 1;
    }
    """

    def compose(self) -> ComposeResult:
        with Vertical(id="help-container"):
            yield Static(" Keyboard Shortcuts ", id="help-title")
            table = DataTable(id="help-table", show_cursor=False)
            yield table
            yield Static("Press [bold]?[/bold] or [bold]Esc[/bold] to close", id="help-footer")

    def on_mount(self) -> None:
        table = self.query_one("#help-table", DataTable)
        table.add_columns("Key", "Where", "Action")
        for key, where, action in _BINDINGS_TABLE:
            table.add_row(
                f"[bold $primary]{key}[/]",
                f"[dim]{where}[/]",
                action,
            )

    def action_dismiss_help(self) -> None:
        self.app.pop_screen()
