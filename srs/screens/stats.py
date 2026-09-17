"""Stats & Analytics screen for cram TUI."""

from __future__ import annotations

from collections import defaultdict
from datetime import datetime, timedelta, timezone

from textual.app import ComposeResult
from textual.containers import Horizontal, ScrollableContainer, Vertical
from textual.screen import Screen
from textual.widgets import DataTable, Label, Static

from srs import cards, config
from srs.cards import current_retrievability


# Block characters for sparkline (▁▂▃▄▅▆▇█)
_SPARK_CHARS = "▁▂▃▄▅▆▇█"


def _sparkline(values: list[int]) -> str:
    """Convert a list of daily counts into a sparkline string."""
    if not values or max(values) == 0:
        return "▁" * len(values)
    hi = max(values)
    return "".join(_SPARK_CHARS[min(int(v / hi * 7 + 0.5), 7)] for v in values)


def _bar(count: int, max_count: int, width: int = 12) -> str:
    """Build an ASCII progress bar proportional to count."""
    if max_count == 0:
        return " " * width
    filled = max(1, round(count / max_count * width)) if count > 0 else 0
    return "█" * filled + "░" * (width - filled)


def _build_topic_rows(all_cards: list[dict]) -> list[tuple[str, int, str, str]]:
    """Return (topic, card_count, pass_rate_str, bar_str) rows sorted by count."""
    topic_counts: dict[str, int] = defaultdict(int)
    topic_pass: dict[str, list[int]] = defaultdict(list)

    for card in all_cards:
        topic = card.get("topic", "General") or "General"
        topic_counts[topic] += 1
        for rev in card.get("reviews", []):
            topic_pass[topic].append(1 if rev.get("rating", 0) >= 3 else 0)

    if not topic_counts:
        return []

    max_count = max(topic_counts.values())
    rows = []
    for topic, count in sorted(topic_counts.items(), key=lambda x: -x[1]):
        ratings = topic_pass[topic]
        if ratings:
            rate = sum(ratings) / len(ratings) * 100
            rate_str = f"{rate:.0f}%"
        else:
            rate_str = "—"
        bar = _bar(count, max_count)
        rows.append((topic, count, rate_str, bar))
    return rows


def _build_activity(all_cards: list[dict]) -> tuple[list[int], int, int]:
    """Return (daily_counts_30d, reviews_this_week, reviews_this_month)."""
    now = datetime.now(timezone.utc)
    day_counts: dict[int, int] = defaultdict(int)  # days_ago → count

    week_total = 0
    month_total = 0

    for card in all_cards:
        for rev in card.get("reviews", []):
            ts = rev.get("reviewed_at", "")
            if not ts:
                continue
            try:
                dt = datetime.fromisoformat(ts.replace("Z", "+00:00"))
                days_ago = (now - dt).days
                if 0 <= days_ago < 30:
                    day_counts[days_ago] += 1
                    month_total += 1
                    if days_ago < 7:
                        week_total += 1
            except (ValueError, TypeError):
                continue

    # Build list: index 0 = 29 days ago, index 29 = today
    daily = [day_counts[29 - i] for i in range(30)]
    return daily, week_total, month_total


def _build_retention_rows(all_cards: list[dict]) -> tuple[list[tuple], list[tuple]]:
    """Return (low_ret_rows, most_lapsed_rows) — top-5 each."""
    scored = []
    for card in all_cards:
        ret = current_retrievability(card)
        lapses = card.get("lapses", 0)
        title = card.get("title", "Untitled")[:40]
        ctype = card.get("type", "problem")
        scored.append((title, ctype, ret, lapses))

    # Top 5 lowest retrievability (exclude new cards at 100%)
    reviewed = [s for s in scored if s[2] < 100.0]
    low_ret = sorted(reviewed, key=lambda x: x[2])[:5]
    low_ret_rows = [(t, ty, f"{r:.1f}%") for t, ty, r, _ in low_ret]

    # Top 5 most lapses
    most_lapsed = sorted(scored, key=lambda x: -x[3])[:5]
    lapsed_rows = [(t, ty, str(lp)) for t, ty, _, lp in most_lapsed if most_lapsed[0][3] > 0]

    return low_ret_rows, lapsed_rows


class StatsScreen(Screen):
    """Full-screen Stats & Analytics view."""

    BINDINGS = [
        ("escape", "go_back", "Back"),
        ("r", "refresh_stats", "Refresh"),
    ]

    def compose(self) -> ComposeResult:
        with Vertical(id="stats-container"):
            yield Static("", id="stats-title")
            yield Static("", id="stats-summary-bar")
            with Horizontal(id="stats-middle"):
                with Vertical(id="stats-topic-pane"):
                    yield Label("Per-Topic Breakdown", id="stats-topic-label")
                    yield DataTable(id="stats-topic-table", show_cursor=False)
                with Vertical(id="stats-activity-pane"):
                    yield Label("Review Activity — last 30 days", id="stats-activity-label")
                    yield Static("", id="stats-sparkline")
                    yield Static("", id="stats-activity-meta")
            with ScrollableContainer(id="stats-health-pane"):
                yield Label("Retention & Health", id="stats-health-label")
                with Horizontal(id="stats-health-tables"):
                    with Vertical(id="stats-ret-wrap"):
                        yield Label("Lowest Retrievability (top 5)", id="stats-ret-label")
                        yield DataTable(id="stats-ret-table", show_cursor=False)
                    with Vertical(id="stats-lapse-wrap"):
                        yield Label("Most Lapses (top 5)", id="stats-lapse-label")
                        yield DataTable(id="stats-lapse-table", show_cursor=False)
        yield Static(
            "  escape: back   r: refresh",
            id="stats-footer",
        )

    def on_mount(self) -> None:
        self._setup_tables()
        self._load_and_render()

    def _setup_tables(self) -> None:
        topic_tbl = self.query_one("#stats-topic-table", DataTable)
        topic_tbl.add_columns("Topic", "Cards", "Pass%", "Bar")

        ret_tbl = self.query_one("#stats-ret-table", DataTable)
        ret_tbl.add_columns("Title", "Type", "Ret%")

        lapse_tbl = self.query_one("#stats-lapse-table", DataTable)
        lapse_tbl.add_columns("Title", "Type", "Lapses")

    def _load_and_render(self) -> None:
        data = cards.load_cards(config.cards_file())
        stats = cards.compute_stats(data)

        all_cards: list[dict] = []
        for key in ("problem_cards", "concept_cards"):
            all_cards.extend(data.get(key, []))

        # ── Title
        self.query_one("#stats-title", Static).update(
            "[bold]cram  Stats & Analytics[/bold]"
        )

        # ── Summary bar
        self.query_one("#stats-summary-bar", Static).update(
            f"  Total: [bold]{stats['total']}[/bold]"
            f"   Due: [bold yellow]{stats['due']}[/bold yellow]"
            f"   New: [bold cyan]{stats['new']}[/bold cyan]"
            f"   Reviewed: [bold green]{stats['reviewed']}[/bold green]"
            f"   Avg Interval: [bold]{stats['avg_interval']}d[/bold]"
        )

        # ── Topic table
        topic_tbl = self.query_one("#stats-topic-table", DataTable)
        topic_tbl.clear()
        for row in _build_topic_rows(all_cards):
            topic, count, rate_str, bar = row
            topic_tbl.add_row(topic, str(count), rate_str, bar)
        if not all_cards:
            topic_tbl.add_row("(no cards yet)", "—", "—", "")

        # ── Sparkline
        daily, week_total, month_total = _build_activity(all_cards)
        now = datetime.now(timezone.utc)

        spark = _sparkline(daily)
        # Label every 7 days: build an annotation line
        label_line = ""
        for i in range(0, 30, 7):
            day_dt = now - timedelta(days=29 - i)
            label = day_dt.strftime("%m/%d")
            # position char i in the sparkline string
            label_line += label.ljust(7)
        label_line = label_line[:30]  # clamp

        self.query_one("#stats-sparkline", Static).update(
            f"[bold]{spark}[/bold]\n[dim]{label_line}[/dim]"
        )
        self.query_one("#stats-activity-meta", Static).update(
            f"  This week: [bold]{week_total}[/bold] reviews"
            f"   This month: [bold]{month_total}[/bold] reviews"
        )

        # ── Retention & health tables
        low_ret_rows, lapsed_rows = _build_retention_rows(all_cards)

        ret_tbl = self.query_one("#stats-ret-table", DataTable)
        ret_tbl.clear()
        if low_ret_rows:
            for title, ctype, ret_str in low_ret_rows:
                ret_tbl.add_row(title, ctype, ret_str)
        else:
            ret_tbl.add_row("(no reviewed cards)", "", "")

        lapse_tbl = self.query_one("#stats-lapse-table", DataTable)
        lapse_tbl.clear()
        if lapsed_rows:
            for title, ctype, lapses in lapsed_rows:
                lapse_tbl.add_row(title, ctype, lapses)
        else:
            lapse_tbl.add_row("(no lapses recorded)", "", "")

    # ── Actions ──────────────────────────────────────────────────────

    def action_go_back(self) -> None:
        self.app.pop_screen()

    def action_refresh_stats(self) -> None:
        self._load_and_render()
        self.notify("Stats refreshed", timeout=2)
