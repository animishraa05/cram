"""Rating widget — Again / Hard / Good / Easy buttons with theme styling."""

from __future__ import annotations

from textual.app import ComposeResult
from textual.containers import Horizontal
from textual.message import Message
from textual.widget import Widget
from textual.widgets import Button, Static


class Rating(Widget):
    """Four-button rating widget for FSRS reviews."""

    class Rated(Message):
        def __init__(self, grade: int) -> None:
            self.grade = grade
            super().__init__()

    def compose(self) -> ComposeResult:
        with Horizontal(id="rating-bar"):
            yield Static("[1]", id="key-again")
            yield Button("Again", id="rate-again", variant="error")
            yield Static("[2]", id="key-hard")
            yield Button("Hard", id="rate-hard", variant="warning")
            yield Static("[3]", id="key-good")
            yield Button("Good", id="rate-good", variant="primary")
            yield Static("[4]", id="key-easy")
            yield Button("Easy", id="rate-easy", variant="success")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        mapping = {
            "rate-again": 1,
            "rate-hard": 2,
            "rate-good": 3,
            "rate-easy": 4,
        }
        grade = mapping.get(event.button.id)
        if grade is not None:
            self.post_message(self.Rated(grade))
