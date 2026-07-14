"""Home screen — main menu for cram TUI."""

from __future__ import annotations

from textual.app import ComposeResult
from textual.containers import Vertical
from textual.screen import Screen
from textual.widgets import Label, ListItem, ListView, Static

from srs import cards, config


class HomeScreen(Screen):
    """Home screen with styled title bar and menu."""

    CSS = """
    #home-container {
        padding: 2;
    }
    #home-title {
        text-style: bold;
        color: white;
        background: $primary;
        padding: 0 1;
        margin-left: 2;
        width: 100%;
    }
    #home-subtitle {
        color: $text-muted;
        padding: 0 0 0 2;
        width: 100%;
        margin-bottom: 1;
    }
    #home-menu {
        border: solid $panel;
    }
    #home-menu ListItem {
        padding: 0 2;
    }
    #home-stats {
        color: $text-muted;
        padding: 1 0 0 2;
        width: 100%;
    }
    #home-footer {
        color: $text-muted;
        padding: 0 0 0 2;
        dock: bottom;
        width: 100%;
    }
    """

    def compose(self) -> ComposeResult:
        with Vertical(id="home-container"):
            yield Static("  cram", id="home-title")
            yield Static("  spaced repetition for problems & concepts", id="home-subtitle")
            yield ListView(
                ListItem(Label("Add Problem")),
                ListItem(Label("Add Concept")),
                ListItem(Label("Review Due")),
                ListItem(Label("Sync LeetCode")),
                ListItem(Label("Settings")),
                id="home-menu",
            )
            yield Static("", id="home-stats")
        yield Static("  1: Add Problem  ·  2: Add Concept  ·  3: Review  ·  ,: Settings  ·  q: Quit", id="home-footer")

    def on_mount(self) -> None:
        self._update_stats()

    def _update_stats(self) -> None:
        data = cards.load_cards(config.cards_file())
        due = cards.get_due_cards(data)
        total = len(data.get("problem_cards", [])) + len(data.get("concept_cards", []))
        stats = self.query_one("#home-stats", Static)
        if total == 0:
            stats.update("  No cards yet. Add a problem or concept to get started.")
        else:
            due_str = f"{len(due)} due" if len(due) > 0 else "all caught up"
            stats.update(f"  {total} cards  ·  {due_str}")

    def on_list_view_selected(self, event: ListView.Selected) -> None:
        match event.index:
            case 0:
                self.app.push_screen("add-problem")
            case 1:
                self.app.push_screen("add-concept")
            case 2:
                self.app.push_screen("review")
            case 3:
                self._do_sync()
            case 4:
                self.app.push_screen("settings")

    def _do_sync(self) -> None:
        username = config.leetcode_username()
        if not username:
            self.notify("LEETCODE_USERNAME not set in config", severity="error")
            return

        self.query_one("#home-stats", Static).update("  Syncing...")
        self.run_worker(self._sync_worker, thread=True, exclusive=True)

    def _sync_worker(self) -> None:
        from srs.leetcode import sync_leetcode

        username = config.leetcode_username()
        data = cards.load_cards(config.cards_file())
        count, new = sync_leetcode(username, data)
        if count > 0:
            cards.save_cards(config.cards_file(), data)
            titles = "\n".join(f"  + {c['title']} [{c.get('topic', '')}]" for c in new[:10])
            self.notify(f"Synced {count} new problems:\n{titles}")
        else:
            self.notify("No new problems in last 24h")
        self._update_stats()
