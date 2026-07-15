"""Browse screen — list all cards, search, edit, delete."""

from __future__ import annotations

from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical
from textual.screen import Screen
from textual.widgets import Input, Label, ListItem, ListView, Static

from srs import cards, config


class BrowseScreen(Screen):
    """Browse all cards with search and filter."""

    ESCAPE_TO_MINIMIZE = False

    BINDINGS = [
        ("j", "cursor_down", "Down"),
        ("k", "cursor_up", "Up"),
        ("d", "delete_card", "Delete"),
        ("e", "edit_topic", "Edit Topic"),
        ("y", "confirm_delete", "Confirm Delete"),
        ("slash", "focus_search", "Search"),
        ("escape", "go_back", "Back"),
    ]

    CSS = """
    #browse-container { height: 1fr; }
    #browse-split { height: 1fr; }
    #browse-title {
        text-style: bold;
        color: $foreground;
        padding: 0 1;
        margin-left: 2;
        width: 100%;
        border-bottom: solid $primary;
    }
    #browse-search { margin: 1 2; }
    #browse-filters { padding: 0 2; }
    #browse-list-pane { width: 2fr; min-width: 20; padding: 0 1; }
    #browse-list { border: solid $panel; height: 1fr; }
    #browse-detail-pane {
        width: 1fr; min-width: 20;
        border-left: solid $panel; padding: 0 1;
    }
    #browse-detail-header {
        text-style: bold; color: $foreground;
        padding: 0 1; margin-bottom: 1; width: 100%;
        border-bottom: solid $primary;
    }
    #browse-detail-content { overflow-y: auto; height: 1fr; }
    #browse-status { color: $text-muted; padding: 1 0 0 2; width: 100%; }
    #browse-footer {
        color: $text-muted;
        padding: 0 0 0 2;
        dock: bottom;
        width: 100%;
    }
    """

    def compose(self) -> ComposeResult:
        with Vertical(id="browse-container"):
            yield Static("  Browse Cards", id="browse-title")
            yield Input(
                placeholder="Search by title or topic... (press / to focus)",
                id="browse-search",
            )
            yield Horizontal(
                Static("  j/k: nav  d: delete  e: edit  /: search", id="browse-filters"),
                id="browse-filter-bar",
            )
            with Horizontal(id="browse-split"):
                with Vertical(id="browse-list-pane"):
                    yield ListView(id="browse-list")
                with Vertical(id="browse-detail-pane"):
                    yield Static("Card Detail", id="browse-detail-header")
                    yield Static("", id="browse-detail-content")
                    yield Input(placeholder="New topic...", id="browse-topic-input")
            yield Static("", id="browse-status")
        yield Static(
            "  j/k: navigate  o/Enter: select  d: delete  e: edit  /: search  Esc: back",
            id="browse-footer",
        )

    def on_mount(self) -> None:
        self._filter = "all"
        self._cards: list[dict] = []
        self._selected_card: dict | None = None
        self._pending_delete: dict | None = None
        self.query_one("#browse-topic-input", Input).display = False
        self._refresh_list()

    def _clear_selection(self) -> None:
        self._selected_card = None
        self._pending_delete = None
        self.query_one("#browse-topic-input", Input).display = False
        self.query_one("#browse-detail-header", Static).update("Card Detail")
        self.query_one("#browse-detail-content", Static).update("")

    def _refresh_list(self, clear_detail: bool = True) -> None:
        data = cards.load_cards(config.cards_file())
        all_cards = []
        for key in ("problem_cards", "concept_cards"):
            all_cards.extend(data.get(key, []))

        query = self.query_one("#browse-search", Input).value.strip().lower()
        now_cards = []
        from datetime import datetime, timezone

        now = datetime.now(timezone.utc)

        for c in all_cards:
            if query:
                title = c.get("title", "").lower()
                topic = c.get("topic", "").lower()
                if query not in title and query not in topic:
                    continue

            if self._filter == "due":
                try:
                    nr = datetime.fromisoformat(c.get("next_review", "").replace("Z", "+00:00"))
                    if nr > now:
                        continue
                except (ValueError, TypeError):
                    pass
            if self._filter == "reviewed" and c.get("review_count", 0) == 0:
                continue

            now_cards.append(c)

        self._cards = now_cards
        if clear_detail:
            self._clear_selection()

        items = []
        for c in now_cards:
            topic = c.get("topic", "")
            card_type = c.get("type", "")
            label = c.get("title", "Unknown")
            if topic:
                label += f" [{topic}]"
            if card_type == "concept":
                label = f"(C) {label}"
            items.append(ListItem(Label(label)))

        lv = self.query_one("#browse-list", ListView)
        lv.clear()
        for item in items:
            lv.append(item)

        total = len(all_cards)
        shown = len(now_cards)
        self.query_one("#browse-status", Static).update(f"  Showing {shown}/{total} cards")

        if now_cards:
            lv.index = 0
            lv.focus()

    def action_focus_search(self) -> None:
        self.query_one("#browse-search", Input).focus()

    def action_cursor_down(self) -> None:
        self.query_one("#browse-list", ListView).action_cursor_down()

    def action_cursor_up(self) -> None:
        self.query_one("#browse-list", ListView).action_cursor_up()

    def on_input_changed(self, event: Input.Changed) -> None:
        if event.input.id == "browse-search":
            self._refresh_list(clear_detail=False)

    def on_list_view_selected(self, event: ListView.Selected) -> None:
        if event.index >= len(self._cards):
            return
        card = self._cards[event.index]
        self._selected_card = card
        self._pending_delete = None
        self.query_one("#browse-topic-input", Input).display = False

        lines = [
            f"  Type      {card.get('type', '')}",
            f"  Topic     {card.get('topic', '') or '(none)'}",
            f"  Reviews   {card.get('review_count', 0)}",
            f"  Interval  {card.get('interval', 1)} days",
        ]
        link = card.get("link", "")
        if link:
            lines.append(f"  Link      {link}")
        nr = card.get("next_review", "")
        if nr:
            lines.append(f"  Next rev  {nr[:10]}")

        vault = config.vault()
        folder = card.get("folder") or config.problem_folder()
        filename = card.get("filename", "")
        if filename:
            filepath = vault / folder / filename
            if filepath.exists():
                try:
                    text = filepath.read_text(encoding="utf-8")
                except (OSError, UnicodeDecodeError) as e:
                    text = f"(error reading file: {e})"
                preview = text[:600] + ("..." if len(text) > 600 else "")
                lines.append("")
                lines.append("  --- Note Preview ---")
                lines.append(preview)

        self.query_one("#browse-detail-header", Static).update(f"  {card.get('title', '')}")
        self.query_one("#browse-detail-content", Static).update("\n".join(lines))

    def action_delete_card(self) -> None:
        if self._selected_card:
            self._confirm_delete()

    def _confirm_delete(self) -> None:
        card = self._selected_card
        if not card:
            return
        self._pending_delete = card
        title = card.get("title", "Unknown")
        self.query_one("#browse-detail-content", Static).update(
            f"  Delete '{title}'?\n\n  Press [y] to confirm, [Esc] to cancel"
        )

    def action_confirm_delete(self) -> None:
        if self._pending_delete:
            self._do_delete(self._pending_delete)
            self._pending_delete = None

    def _do_delete(self, card: dict) -> None:
        card_id = card.get("id")
        if not card_id:
            self.notify("Cannot delete: card has no ID", severity="error")
            return
        data = cards.load_cards(config.cards_file())
        for key in ("problem_cards", "concept_cards"):
            before = len(data.get(key, []))
            data[key] = [c for c in data.get(key, []) if c.get("id") != card_id]
            if len(data.get(key, [])) < before:
                break
        cards.save_cards(config.cards_file(), data)
        self.notify(f"Deleted: {card.get('title', '')}")
        self._selected_card = None
        self._refresh_list()

    def action_edit_topic(self) -> None:
        card = self._selected_card
        if not card:
            self.notify("Select a card first")
            return
        self._edit_topic(card)

    def _edit_topic(self, card: dict) -> None:
        topic_input = self.query_one("#browse-topic-input", Input)
        topic_input.value = card.get("topic", "")
        topic_input.display = True
        topic_input.focus()
        self.query_one("#browse-detail-content", Static).update(
            f"  Editing topic for: {card.get('title', '')}\n"
            f"  Enter new topic, then press Enter. Esc to cancel."
        )

    def on_input_submitted(self, event: Input.Submitted) -> None:
        if event.input.id == "browse-topic-input":
            card = self._selected_card
            if not card:
                return
            new_topic = event.input.value.strip()
            data = cards.load_cards(config.cards_file())
            target = cards.find_card_by_id(data, card.get("id", ""))
            if target:
                target["topic"] = new_topic
                cards.save_cards(config.cards_file(), data)
                self.notify(f"Updated topic: {new_topic or '(none)'}")
            self.query_one("#browse-topic-input", Input).display = False
            self._refresh_list()

    def action_go_back(self) -> None:
        topic_input = self.query_one("#browse-topic-input", Input)
        if topic_input.display:
            topic_input.display = False
            self.query_one("#browse-list", ListView).focus()
            return
        if self._pending_delete:
            self._pending_delete = None
            self._refresh_list()
            return
        if self._selected_card:
            self._clear_selection()
            self.query_one("#browse-list", ListView).focus()
            return
        search = self.query_one("#browse-search", Input)
        if search.value:
            search.value = ""
            return
        self.app.pop_screen()
