"""Home screen — main menu for cram TUI."""

from __future__ import annotations

from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical
from textual.screen import Screen
from textual.widgets import Label, ListItem, ListView, Static

from srs import cards, config


class HomeScreen(Screen):
    """Home screen with dashboard telemetry."""

    BINDINGS = [
        ("j", "cursor_down", "Down"),
        ("k", "cursor_up", "Up"),
    ]

    CSS = """
    #home-container {
        padding: 1;
        height: 1fr;
    }
    #home-title {
        text-style: bold;
        color: $foreground;
        padding: 0 1;
        margin-left: 2;
        width: 100%;
        border-bottom: solid $primary;
        margin-bottom: 1;
    }
    #home-split {
        height: 1fr;
    }
    #home-menu-pane {
        width: 35%;
        height: 1fr;
        margin-right: 1;
    }
    #home-menu {
        height: 1fr;
        border: round $panel;
    }
    #home-menu ListView {
        border: none;
    }
    #home-menu ListItem {
        padding: 0 2;
    }
    #home-dashboard-pane {
        width: 65%;
        height: 1fr;
    }
    #home-due-status {
        border: round $panel;
        height: 3;
        background: $surface;
        content-align: center middle;
        margin-bottom: 1;
    }
    #home-stats-grid {
        height: 7;
        margin-bottom: 1;
    }
    #home-stats-details {
        border: round $panel;
        width: 1fr;
        height: 1fr;
        margin-right: 1;
    }
    #home-config-details {
        border: round $panel;
        width: 1fr;
        height: 1fr;
    }
    #home-topics-details {
        border: round $panel;
        height: 6;
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
            yield Static("cram  spaced repetition", id="home-title")
            with Horizontal(id="home-split"):
                with Vertical(id="home-menu-pane"):
                    yield ListView(
                        ListItem(Label("Add Problem")),
                        ListItem(Label("Add Concept")),
                        ListItem(Label("Review Due")),
                        ListItem(Label("Browse Cards")),
                        ListItem(Label("Sync LeetCode")),
                        ListItem(Label("Settings")),
                        id="home-menu",
                    )
                with Vertical(id="home-dashboard-pane"):
                    yield Static("", id="home-due-status")
                    with Horizontal(id="home-stats-grid"):
                        yield Static("", id="home-stats-details")
                        yield Static("", id="home-config-details")
                    yield Static("", id="home-topics-details")
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
        self.query_one("#home-menu", ListView).border_title = " cram menu "
        self.query_one("#home-due-status", Static).border_title = " status "
        self.query_one("#home-stats-details", Static).border_title = " stats "
        self.query_one("#home-config-details", Static).border_title = " system "
        self.query_one("#home-topics-details", Static).border_title = " focus "

    def _on_screen_resume(self, event: object) -> None:  # type: ignore[override]
        self._update_stats()

    def _update_stats(self) -> None:
        data = cards.load_cards(config.cards_file())
        stats = cards.compute_stats(data)

        # 1. Update due status
        try:
            due_status = self.query_one("#home-due-status", Static)
            if stats["due"] > 0:
                due_status.update(f"[bold red][!] {stats['due']} review(s) due[/]")
            else:
                due_status.update("[bold green][x] All caught up[/]")
        except Exception:
            pass

        # 2. Update stats details
        try:
            stats_details = self.query_one("#home-stats-details", Static)
            lines = [
                f"Total Cards : {stats['total']}",
                f"Reviewed    : {stats['reviewed']}",
                f"New Cards   : {stats['new']}",
                f"Avg Interval: {stats['avg_interval']}d",
            ]
            stats_details.update("\n".join(lines))
        except Exception:
            pass

        # 3. Update config details
        try:
            config_details = self.query_one("#home-config-details", Static)
            # Truncate vault path if it's too long
            vault_str = str(config.vault())
            if len(vault_str) > 22:
                vault_str = "..." + vault_str[-19:]
            lines = [
                f"Vault: {vault_str}",
                f"User : {config.leetcode_username() or '(none)'}",
            ]
            config_details.update("\n".join(lines))
        except Exception:
            pass

        # 4. Update topics
        try:
            topics_details = self.query_one("#home-topics-details", Static)
            topics = stats.get("topics", {})
            if topics:
                lines = []
                for topic, count in list(topics.items())[:3]:
                    lines.append(f"* {topic}: {count}")
                topics_details.update("\n".join(lines))
            else:
                topics_details.update("No categories reviewed yet.")
        except Exception:
            pass

    def on_list_view_selected(self, event: ListView.Selected) -> None:
        idx = event.list_view.index
        if idx is not None:
            self._navigate_to(idx)

    def _navigate_to(self, index: int) -> None:
        match index:
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

        self.query_one("#home-due-status", Static).update("Syncing...")
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
