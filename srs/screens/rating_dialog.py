"""Rating dialog — modal popup for FSRS recall rating with vim keybinds."""

from __future__ import annotations

from textual.app import ComposeResult
from textual.containers import Vertical
from textual.screen import ModalScreen
from textual.widgets import Button, Static


class RatingDialog(ModalScreen[int]):
    """Modal dialog to rate recall: Again / Hard / Good / Easy."""

    CSS = """
    RatingDialog {
        align: center middle;
    }
    #rating-dialog-box {
        width: 44;
        height: auto;
        border: round $panel;
        background: $surface;
        padding: 1 2;
    }
    #rating-dialog-title {
        text-style: bold;
        color: $foreground;
        padding: 0 1;
        margin-bottom: 1;
        width: 100%;
        content-align-horizontal: center;
        border-bottom: solid $primary;
    }
    #rating-dialog-hint {
        color: $text-muted;
        margin-top: 1;
        width: 100%;
        content-align-horizontal: center;
    }
    #rating-dialog-buttons {
        height: auto;
    }
    #rating-dialog-buttons Button {
        width: 18;
        margin: 0 1;
    }
    """

    BINDINGS = [
        ("a", "rate(1)", "Again"),
        ("h", "rate(2)", "Hard"),
        ("g", "rate(3)", "Good"),
        ("e", "rate(4)", "Easy"),
        ("escape", "cancel", "Cancel"),
    ]

    def compose(self) -> ComposeResult:
        with Vertical(id="rating-dialog-box"):
            yield Static("  Rate Your Recall", id="rating-dialog-title")
            yield Button("Again [a]", id="rate-again")
            yield Button("Hard [h]", id="rate-hard")
            yield Button("Good [g]", id="rate-good")
            yield Button("Easy [e]", id="rate-easy")
            yield Static("j/k: navigate  o/Enter: pick  Esc: cancel", id="rating-dialog-hint")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        mapping = {
            "rate-again": 1,
            "rate-hard": 2,
            "rate-good": 3,
            "rate-easy": 4,
        }
        grade = mapping.get(event.button.id)
        if grade is not None:
            self.dismiss(grade)

    def action_rate(self, grade: int) -> None:
        self.dismiss(grade)

    def action_cancel(self) -> None:
        self.dismiss(None)
