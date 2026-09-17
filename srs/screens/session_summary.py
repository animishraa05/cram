"""Session summary screen — shown after completing a review session."""

from __future__ import annotations

from textual.app import ComposeResult
from textual.containers import Vertical
from textual.screen import ModalScreen
from textual.widgets import Static


class SessionSummaryScreen(ModalScreen[None]):
    """Modal screen displayed after all cards in a session have been rated."""

    BINDINGS = [
        ("escape", "dismiss_summary", "Close"),
        ("enter", "dismiss_summary", "Close"),
    ]

    CSS = """
    SessionSummaryScreen {
        align: center middle;
        background: $background 75%;
    }
    #summary-container {
        width: 58;
        max-width: 90%;
        height: auto;
        background: $surface;
        border: round $primary;
        padding: 1 2;
    }
    #summary-title {
        text-style: bold;
        color: $foreground;
        padding: 0 1;
        margin-bottom: 1;
        width: 100%;
        content-align-horizontal: center;
        border-bottom: solid $primary;
    }
    #summary-stats {
        width: 100%;
        padding: 0 1;
        margin-bottom: 1;
    }
    #summary-ratings {
        width: 100%;
        padding: 0 1;
        margin-bottom: 1;
        border: round $panel;
    }
    #summary-motivational {
        width: 100%;
        padding: 0 1;
        content-align-horizontal: center;
        margin-bottom: 1;
    }
    #summary-footer {
        color: $text-muted;
        width: 100%;
        content-align-horizontal: center;
        border-top: solid $panel;
        padding-top: 1;
    }
    """

    def __init__(
        self,
        cards_reviewed: int = 0,
        again: int = 0,
        hard: int = 0,
        good: int = 0,
        easy: int = 0,
        avg_interval: float = 0.0,
    ) -> None:
        super().__init__()
        self._cards_reviewed = cards_reviewed
        self._again = again
        self._hard = hard
        self._good = good
        self._easy = easy
        self._avg_interval = avg_interval

    def _motivational_line(self) -> str:
        if self._cards_reviewed == 0:
            return "Get out there and start reviewing! 💪"
        again_ratio = self._again / self._cards_reviewed if self._cards_reviewed else 0.0
        if again_ratio > 0.5:
            return "Keep going — consistency beats perfection! 🧠"
        elif again_ratio > 0.25:
            return "Solid effort! Every review builds the habit. 📈"
        else:
            return "Great session! 🔥"

    def compose(self) -> ComposeResult:
        again = self._again
        hard = self._hard
        good = self._good
        easy = self._easy
        reviewed = self._cards_reviewed
        avg_iv = self._avg_interval

        stats_text = (
            f"  Cards reviewed : [bold]{reviewed}[/bold]\n"
            f"  Avg next interval : [bold]{avg_iv:.1f}d[/bold]"
        )
        ratings_text = (
            f"  [bold red]Again[/]  {again}    "
            f"[bold yellow]Hard[/]  {hard}    "
            f"[bold green]Good[/]  {good}    "
            f"[bold cyan]Easy[/]  {easy}"
        )
        motivational = self._motivational_line()

        with Vertical(id="summary-container"):
            yield Static("Session Complete 🎉", id="summary-title")
            yield Static(stats_text, id="summary-stats")
            yield Static(ratings_text, id="summary-ratings")
            yield Static(motivational, id="summary-motivational")
            yield Static(
                "Press [bold]Enter[/bold] or [bold]Esc[/bold] to return",
                id="summary-footer",
            )

    def action_dismiss_summary(self) -> None:
        self.dismiss(None)
