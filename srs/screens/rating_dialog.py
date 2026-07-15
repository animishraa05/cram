"""Rating dialog — modal popup for FSRS recall rating with vim keybinds."""

from __future__ import annotations

from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical
from textual.screen import ModalScreen
from textual.widgets import Button, Static


class RatingDialog(ModalScreen[int]):
    """Modal dialog to rate recall: Again / Hard / Good / Easy with projected intervals."""

    CSS = """
    RatingDialog {
        align: center middle;
    }
    #rating-dialog-box {
        width: 78;
        height: auto;
        border: round $primary;
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
        align: center middle;
        content-align: center middle;
    }
    #rating-dialog-buttons Button {
        width: 17;
        margin: 0 1;
        background: $panel;
        color: $text;
        border: round $panel;
    }
    #rating-dialog-buttons Button:focus {
        background: $accent 15%;
        color: $foreground;
        border: double $accent;
        text-style: bold;
    }
    """

    BINDINGS = [
        ("a", "rate(1)", "Again"),
        ("h", "rate(2)", "Hard"),
        ("g", "rate(3)", "Good"),
        ("e", "rate(4)", "Easy"),
        ("escape", "cancel", "Cancel"),
        ("left", "move_focus(-1)", "Focus Left"),
        ("right", "move_focus(1)", "Focus Right"),
    ]

    def __init__(self, card: dict | None = None, desired_retention: float = 0.9) -> None:
        super().__init__()
        self.card = card
        self.desired_retention = desired_retention

    def compose(self) -> ComposeResult:
        intervals = {}
        if self.card:
            from srs.cards import predict_next_intervals

            try:
                intervals = predict_next_intervals(self.card, self.desired_retention)
            except Exception:
                pass

        def label(name: str, key: str, grade: int) -> str:
            if grade in intervals:
                days = intervals[grade]
                suffix = f"{days}d" if days > 0 else "1d"
                return f"{name} [{key}] ({suffix})"
            return f"{name} [{key}]"

        with Vertical(id="rating-dialog-box"):
            yield Static("Rate Your Recall", id="rating-dialog-title")
            with Horizontal(id="rating-dialog-buttons"):
                yield Button(label("Again", "a", 1), id="rate-again")
                yield Button(label("Hard", "h", 2), id="rate-hard")
                yield Button(label("Good", "g", 3), id="rate-good")
                yield Button(label("Easy", "e", 4), id="rate-easy")
            yield Static("a/h/g/e: rate  Esc: cancel", id="rating-dialog-hint")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        mapping = {
            "rate-again": 1,
            "rate-hard": 2,
            "rate-good": 3,
            "rate-easy": 4,
        }
        grade = mapping.get(event.button.id or "")
        if grade is not None:
            self.dismiss(grade)

    def action_rate(self, grade: int) -> None:
        self.dismiss(grade)

    def action_cancel(self) -> None:
        self.dismiss(None)

    def action_move_focus(self, direction: int) -> None:
        buttons = [
            self.query_one("#rate-again", Button),
            self.query_one("#rate-hard", Button),
            self.query_one("#rate-good", Button),
            self.query_one("#rate-easy", Button),
        ]
        focused = self.app.focused
        current_idx = 0
        for idx, btn in enumerate(buttons):
            if btn == focused:
                current_idx = idx
                break
        else:
            current_idx = 2  # Default focus on Good

        new_idx = (current_idx + direction) % len(buttons)
        buttons[new_idx].focus()
