"""Confirm dialog — reusable modal for yes/no confirmations."""

from __future__ import annotations

from textual.app import ComposeResult
from textual.containers import Vertical
from textual.screen import ModalScreen
from textual.widgets import Button, Static


class ConfirmScreen(ModalScreen[bool]):
    """Modal dialog for yes/no confirmation."""

    CSS = """
    ConfirmScreen {
        align: center middle;
    }
    #confirm-dialog-box {
        width: 40;
        height: auto;
        border: round $panel;
        background: $surface;
        padding: 1 2;
    }
    #confirm-dialog-title {
        text-style: bold;
        color: $foreground;
        padding: 0 1;
        margin-bottom: 1;
        width: 100%;
        content-align-horizontal: center;
        border-bottom: solid $primary;
    }
    #confirm-dialog-message {
        width: 100%;
        margin-bottom: 1;
        content-align-horizontal: center;
    }
    #confirm-dialog-hint {
        color: $text-muted;
        margin-top: 1;
        width: 100%;
        content-align-horizontal: center;
    }
    #confirm-dialog-buttons {
        height: auto;
    }
    #confirm-dialog-buttons Button {
        width: 16;
        margin: 0 1;
    }
    """

    BINDINGS = [
        ("y", "confirm", "Yes"),
        ("n", "cancel", "No"),
        ("escape", "cancel", "Cancel"),
    ]

    def __init__(self, message: str = "Are you sure?") -> None:
        super().__init__()
        self._message = message

    def compose(self) -> ComposeResult:
        with Vertical(id="confirm-dialog-box"):
            yield Static("  Confirm", id="confirm-dialog-title")
            yield Static(self._message, id="confirm-dialog-message")
            yield Button("Yes [y]", id="confirm-yes")
            yield Button("No [n]", id="confirm-no")
            yield Static("y/n: pick  Esc: cancel", id="confirm-dialog-hint")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "confirm-yes":
            self.dismiss(True)
        else:
            self.dismiss(False)

    def action_confirm(self) -> None:
        self.dismiss(True)

    def action_cancel(self) -> None:
        self.dismiss(False)
