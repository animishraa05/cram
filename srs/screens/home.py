"""Home screen — main menu for cram TUI."""

from __future__ import annotations

from textual.app import ComposeResult
from textual.containers import Vertical
from textual.screen import Screen
from textual.widgets import Label, ListItem, ListView, Static

from srs import cards, config


class HomeScreen(Screen):
    """Home screen with styled title bar and menu."""

    BINDINGS = [
        ("j", "cursor_down", "Down"),
        ("k", "cursor_up", "Up"),
    ]

    CSS = """
    #home-container {
        padding: 2;
    }
    #home-title {
        text-style: bold;
        color: $foreground;
        padding: 0 1;
        margin-left: 2;
        width: 100%;
        border-bottom: solid $primary;
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
                ListItem(Label("Browse Cards")),
                ListItem(Label("Sync LeetCode")),
                ListItem(Label("Settings")),
                id="home-menu",
            )
            yield Static("", id="home-stats")
        yield Static(
            "  j/k: navigate  o/Enter: select  q: quit",
            id="home-footer",
        )

    def action_cursor_down(self) -> None:
        self.query_one("#home-menu", ListView).action_cursor_down()

    def action_cursor_up(self) -> None:
        self.query_one("#home-menu", ListView).action_cursor_up()

    def on_mount(self) -> None:
        self._update_stats()

    def on_screen_resume(self) -> None:
        self._update_stats()

    def _update_stats(self) -> None:
        data = cards.load_cards(config.cards_file())
        stats = cards.compute_stats(data)
        try:
            stats_line = self.query_one("#home-stats", Static)
        except Exception:
            return
        if stats["total"] == 0:
            stats_line.update("  No cards yet. Add a problem or concept to get started.")
        else:
            due_str = f"{stats['due']} due" if stats["due"] > 0 else "all caught up"
            parts = [f"{stats['total']} cards", due_str]
            if stats["new"] > 0:
                parts.append(f"{stats['new']} new")
            topics = stats.get("topics", {})
            if topics:
                top = list(topics.items())[:3]
                topic_str = ", ".join(f"{t}({n})" for t, n in top)
                parts.append(f"top: {topic_str}")
            stats_line.update("  " + "  ·  ".join(parts))

    def on_list_view_selected(self, event: ListView.Selected) -> None:
        match event.index:
            case 0:
                self.app.push_screen("add-problem")
            case 1:
                self.app.push_screen("add-concept")
            case 2:
                self.app.push_screen("review")
            case 3:
                self.app.push_screen("browse")
            case 4:
                self._do_sync()
            case 5:
                self.app.push_screen("settings")

    def _do_sync(self) -> None:
        username = config.leetcode_username()
        if not username:
            self.notify("LEETCODE_USERNAME not set in config", severity="error")
            return

        self.query_one("#home-stats", Static).update("  Syncing...")
        self.run_worker(self._sync_worker, thread=True, exclusive=True)

    def _sync_worker(self) -> None:
        from srs.leetcode import LeetCodeAPIError, sync_leetcode

        username = config.leetcode_username()
        data = cards.load_cards(config.cards_file())
        try:
            count, new = sync_leetcode(username, data)
        except LeetCodeAPIError as e:
            self.app.call_from_thread(self.notify, f"Sync failed: {e}", severity="error")
            self.app.call_from_thread(self._update_stats)
            return
        if count > 0:
            cards.save_cards(config.cards_file(), data)
            titles = "\n".join(
                f"  + {c.get('title', 'Unknown')} [{c.get('topic', '')}]" for c in new[:10]
            )
            self.app.call_from_thread(self.notify, f"Synced {count} new problems:\n{titles}")
        else:
            self.app.call_from_thread(self.notify, "No new problems in last 24h")
        self.app.call_from_thread(self._update_stats)
