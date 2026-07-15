"""Review screen — show due cards, pick one, read note, rate via dialog."""

from __future__ import annotations

from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical
from textual.screen import Screen
from textual.widgets import Label, ListItem, ListView, Static

from srs import cards, config


class ReviewScreen(Screen):
    """Review screen with split pane layout."""

    ESCAPE_TO_MINIMIZE = False

    BINDINGS = [
        ("j", "cursor_down", "Down"),
        ("k", "cursor_up", "Up"),
        ("n", "skip_card", "Skip"),
        ("escape", "go_back", "Back"),
    ]

    CSS = """
    #review-container {
        height: 1fr;
    }
    #review-split {
        height: 1fr;
    }
    #review-title {
        text-style: bold;
        color: $foreground;
        padding: 0 1;
        margin-left: 2;
        width: 100%;
        border-bottom: solid $primary;
    }
    #review-list-pane {
        width: 1fr;
        min-width: 20;
        padding: 0 1;
    }
    #review-list {
        border: solid $panel;
        height: 1fr;
    }
    #review-preview-pane {
        width: 1fr;
        min-width: 20;
        border-left: solid $panel;
        padding: 0 1;
    }
    #review-preview-header {
        text-style: bold;
        color: $foreground;
        padding: 0 1;
        margin-bottom: 1;
        width: 100%;
        border-bottom: solid $primary;
    }
    #review-preview-content {
        overflow-y: auto;
        height: 1fr;
    }
    #review-preview-footer {
        color: $text-muted;
        padding: 1 0 0 0;
        width: 100%;
        border-top: solid $panel;
        margin-top: 1;
    }
    #review-status {
        color: $text-muted;
        padding: 1 0 0 2;
        width: 100%;
    }
    #review-footer {
        color: $text-muted;
        padding: 0 0 0 2;
        dock: bottom;
        width: 100%;
    }
    """

    def compose(self) -> ComposeResult:
        with Vertical(id="review-container"):
            yield Static("  Review Due", id="review-title")
            with Horizontal(id="review-split"):
                with Vertical(id="review-list-pane"):
                    yield ListView(id="review-list")
                with Vertical(id="review-preview-pane"):
                    yield Static("Note Preview", id="review-preview-header")
                    yield Static("", id="review-preview-content")
                    yield Static("", id="review-preview-footer")
            yield Static("", id="review-status")
        yield Static(
            "  j/k: navigate  o/Enter: rate  n: skip  Esc: back",
            id="review-footer",
        )

    def on_mount(self) -> None:
        self._populate_due()

    def _populate_due(self) -> None:
        data = cards.load_cards(config.cards_file())
        self._due = cards.get_due_cards(data)

        if not self._due:
            all_cards = []
            for key in ("problem_cards", "concept_cards"):
                all_cards.extend(data.get(key, []))

            if all_cards:
                from datetime import datetime, timezone

                now = datetime.now(timezone.utc)
                future = []
                for c in all_cards:
                    try:
                        nr = datetime.fromisoformat(c.get("next_review", "").replace("Z", "+00:00"))
                        if nr > now:
                            future.append(nr)
                    except Exception:
                        pass

                if future:
                    next_up = min(future)
                    delta = next_up - now
                    hours = int(delta.total_seconds() // 3600)
                    if hours < 1:
                        msg = "  No cards due now. Next review in less than an hour."
                    elif hours < 24:
                        msg = f"  No cards due now. Next review in {hours}h."
                    else:
                        days = hours // 24
                        msg = f"  No cards due now. Next review in {days}d."
                else:
                    msg = "  No cards due for review! Great work."
            else:
                msg = "  No cards yet. Add a problem or concept to get started."

            self.query_one("#review-status", Static).update(msg)
            return

        items = []
        for c in self._due:
            topic = c.get("topic", "")
            card_type = c.get("type", "")
            label = c.get("title", "Unknown")
            if topic:
                label += f" [{topic}]"
            if card_type == "concept":
                label = f"(concept) {label}"
            items.append(ListItem(Label(label)))

        lv = self.query_one("#review-list", ListView)
        lv.clear()
        for item in items:
            lv.append(item)
        if self._due:
            lv.index = 0
            lv.focus()

    def action_cursor_down(self) -> None:
        self.query_one("#review-list", ListView).action_cursor_down()

    def action_cursor_up(self) -> None:
        self.query_one("#review-list", ListView).action_cursor_up()

    def on_list_view_selected(self, event: ListView.Selected) -> None:
        idx = event.index
        if idx >= len(getattr(self, "_due", [])):
            return
        card = self._due[idx]
        self._rating_card_id = card.get("id")

        vault = config.vault()
        folder = card.get("folder") or config.problem_folder()
        filename = card.get("filename", "")
        if not filename:
            from srs.templates import sanitize_filename

            filename = sanitize_filename(card.get("title", "untitled")) + ".md"
        filepath = vault / folder / filename

        topic = card.get("topic", "")
        label = f"  {card.get('title', 'Unknown')}"
        if topic:
            label += f" [{topic}]"
        self.query_one("#review-preview-header", Static).update(label)

        if filepath.exists():
            try:
                text = filepath.read_text(encoding="utf-8")
            except (OSError, UnicodeDecodeError) as e:
                text = f"(error reading file: {e})"
            preview = text[:800] + ("..." if len(text) > 800 else "")
            self.query_one("#review-preview-content", Static).update(preview)
        else:
            self.query_one("#review-preview-content", Static).update("  (note file not found)")

        self.query_one("#review-status", Static).update("  Rate your recall:")
        from srs.screens.rating_dialog import RatingDialog

        self.app.push_screen(RatingDialog(), self._on_rate_result)

    def _on_rate_result(self, grade: int | None) -> None:
        if grade is None:
            self.query_one("#review-status", Static).update("  Rating cancelled.")
            self.query_one("#review-list", ListView).focus()
            return

        data = cards.load_cards(config.cards_file())
        card_id = getattr(self, "_rating_card_id", None)
        if not card_id:
            return

        target = cards.find_card_by_id(data, card_id)
        if target:
            cards.update_card(target, grade, config.desired_retention())
            cards.save_cards(config.cards_file(), data)
            self.notify(f"Rated {target.get('title', 'Unknown')}: grade={grade}")

        self._populate_due()
        if not self._due:
            self.app.pop_screen()

    def action_skip_card(self) -> None:
        if not self._due:
            return
        self.query_one("#review-status", Static).update("  Skipped.")
        lv = self.query_one("#review-list", ListView)
        idx = lv.index
        if idx is not None and idx < len(self._due):
            self._due.pop(idx)
            items = []
            for c in self._due:
                topic = c.get("topic", "")
                card_type = c.get("type", "")
                label = c.get("title", "Unknown")
                if topic:
                    label += f" [{topic}]"
                if card_type == "concept":
                    label = f"(concept) {label}"
                items.append(ListItem(Label(label)))
            lv.clear()
            for item in items:
                lv.append(item)
            if self._due:
                lv.index = min(idx, len(self._due) - 1)
                lv.focus()
            else:
                self.app.pop_screen()

    def action_go_back(self) -> None:
        self.app.pop_screen()
