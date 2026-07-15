"""Confirm dialog — reusable modal for yes/no confirmations."""

from __future__ import annotations

from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical
from textual.screen import ModalScreen
from textual.widgets import Button, Static


class ConfirmScreen(ModalScreen[bool]):
    """Modal dialog for yes/no confirmation with horizontal buttons and arrow key navigation."""

    CSS = """
    ConfirmScreen {
        align: center middle;
    }
    #confirm-dialog-box {
        width: 44;
        height: auto;
        border: round $primary;
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
        align: center middle;
        content-align: center middle;
    }
    #confirm-dialog-buttons Button {
        width: 16;
        margin: 0 1;
        background: $panel;
        color: $text;
        border: round $panel;
    }
    #confirm-dialog-buttons Button:focus {
        background: $accent 15%;
        color: $foreground;
        border: double $accent;
        text-style: bold;
    }
    """

    BINDINGS = [
        ("y", "confirm", "Yes"),
        ("n", "cancel", "No"),
        ("escape", "cancel", "Cancel"),
        ("left", "move_focus(-1)", "Focus Left"),
        ("right", "move_focus(1)", "Focus Right"),
    ]

    def __init__(self, message: str = "Are you sure?") -> None:
        super().__init__()
        self._message = message

    def compose(self) -> ComposeResult:
        with Vertical(id="confirm-dialog-box"):
            yield Static("Confirm", id="confirm-dialog-title")
            yield Static(self._message, id="confirm-dialog-message")
            with Horizontal(id="confirm-dialog-buttons"):
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

    def action_move_focus(self, direction: int) -> None:
        buttons = [
            self.query_one("#confirm-yes", Button),
            self.query_one("#confirm-no", Button),
        ]
        focused = self.app.focused
        current_idx = 0
        for idx, btn in enumerate(buttons):
            if btn == focused:
                current_idx = idx
                break
        else:
            current_idx = 0

        new_idx = (current_idx + direction) % len(buttons)
        buttons[new_idx].focus()
