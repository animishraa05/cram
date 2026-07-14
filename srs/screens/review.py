"""Review screen — show due cards, pick one, open nvim, rate."""

from __future__ import annotations

import subprocess
import shutil

from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical
from textual.screen import Screen
from textual.widgets import Label, ListItem, ListView, Static

from srs import cards, config
from srs.screens.rating import Rating


class ReviewScreen(Screen):
    """Review screen with split pane layout."""

    ESCAPE_TO_MINIMIZE = False

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
            yield Rating()

    def on_mount(self) -> None:
        self.query_one(Rating).display = False
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
                        nr = datetime.fromisoformat(c["next_review"].replace("Z", "+00:00"))
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
            label = c["title"]
            if topic:
                label += f" [{topic}]"
            if card_type == "concept":
                label = f"(concept) {label}"
            items.append(ListItem(Label(label)))

        lv = self.query_one("#review-list", ListView)
        lv.clear()
        for item in items:
            lv.append(item)

    def on_list_view_selected(self, event: ListView.Selected) -> None:
        idx = event.index
        if idx >= len(getattr(self, "_due", [])):
            return
        card = self._due[idx]
        self._open_nvim(card)

    def _open_nvim(self, card: dict) -> None:
        vault = config.vault()
        folder = card.get("folder", config.problem_folder())
        filename = card.get("filename", "")

        if not filename:
            from srs.templates import sanitize_filename
            filename = sanitize_filename(card["title"]) + ".md"

        filepath = vault / folder / filename

        if not filepath.exists():
            self.query_one("#review-status", Static).update(
                f"  Note not found: {filepath}"
            )
            return

        text = filepath.read_text()
        preview = text[:800] + ("..." if len(text) > 800 else "")
        self.query_one("#review-preview-content", Static).update(preview)
        self.query_one("#review-preview-header", Static).update(f"  {filepath.name}")
        self.query_one("#review-status", Static).update(f"  Reviewing: {filepath.name}")

        if not shutil.which("nvim"):
            self.notify("nvim not found in PATH. Install neovim first.", severity="error")
            self.query_one(Rating).display = True
            self.query_one("#review-status", Static).update("  Rate your recall (nvim unavailable):")
            return

        self.app.suspend()
        try:
            subprocess.run(["nvim", str(filepath)])
        finally:
            self.app.resume()

        text = filepath.read_text()
        preview = text[:800] + ("..." if len(text) > 800 else "")
        self.query_one("#review-preview-content", Static).update(preview)
        self.query_one(Rating).display = True
        self.query_one("#review-status", Static).update("  Rate your recall:")

    def key_1(self) -> None:
        if self.query_one(Rating).display:
            self.post_message(Rating.Rated(1))

    def key_2(self) -> None:
        if self.query_one(Rating).display:
            self.post_message(Rating.Rated(2))

    def key_3(self) -> None:
        if self.query_one(Rating).display:
            self.post_message(Rating.Rated(3))

    def key_4(self) -> None:
        if self.query_one(Rating).display:
            self.post_message(Rating.Rated(4))

    def key_escape(self) -> None:
        self.app.pop_screen()

    def on_rating_rated(self, event: Rating.Rated) -> None:
        data = cards.load_cards(config.cards_file())
        idx = self.query_one("#review-list").index
        if idx >= len(self._due):
            return

        card_id = self._due[idx].get("id")
        target = cards.find_card_by_id(data, card_id)
        if target:
            cards.update_card(target, event.grade, config.desired_retention())
            cards.save_cards(config.cards_file(), data)
            self.notify(f"Rated {target['title']}: grade={event.grade}")

        self.app.pop_screen()
