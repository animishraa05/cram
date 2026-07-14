"""cram main application — Textual TUI with CLI argument support."""

from __future__ import annotations

import sys

from textual.app import App

from srs.config import is_configured, theme_name
from srs.theme import THEMES
from srs.screens.home import HomeScreen
from srs.screens.add_problem import AddProblemScreen
from srs.screens.add_concept import AddConceptScreen
from srs.screens.review import ReviewScreen
from srs.screens.setup import SetupScreen
from srs.screens.settings import SettingsScreen


class CramApp(App):
    TITLE = "cram"
    SUB_TITLE = "spaced repetition for problems & concepts"
    CSS_PATH = "cram.tcss"

    SCREENS = {
        "home": HomeScreen,
        "add-problem": AddProblemScreen,
        "add-concept": AddConceptScreen,
        "review": ReviewScreen,
        "setup": SetupScreen,
        "settings": SettingsScreen,
    }

    BINDINGS = [
        ("q", "quit", "Quit"),
        ("1", "switch_screen('add-problem')", "Add Problem"),
        ("2", "switch_screen('add-concept')", "Add Concept"),
        ("3", "switch_screen('review')", "Review"),
        ("comma", "open_settings", "Settings"),
    ]

    def __init__(self, cli_target: str | None = None) -> None:
        super().__init__()
        self._cli_target = cli_target

    def action_open_settings(self) -> None:
        self.push_screen("settings")

    def on_mount(self) -> None:
        self._register_themes()
        if not is_configured():
            self.push_screen("setup")
        elif self._cli_target:
            self.push_screen(self._cli_target)
        else:
            self.push_screen("home")

    def _register_themes(self) -> None:
        from textual.theme import Theme as TTheme

        for name, t in THEMES.items():
            textual_theme = TTheme(
                name=f"cram-{name}",
                primary=t.primary,
                secondary=t.secondary,
                accent=t.accent,
                panel=t.border,
            )
            self.register_theme(textual_theme)
        self.theme = f"cram-{theme_name()}"


def main() -> None:
    args = sys.argv[1:]

    # Handle non-TUI subcommands
    if args and args[0] == "sync":
        from srs.config import leetcode_username, cards_file
        from srs.cards import load_cards, save_cards
        from srs.leetcode import sync_leetcode

        username = leetcode_username()
        if not username:
            print("Error: LEETCODE_USERNAME not set in ~/.config/cram/config", file=sys.stderr)
            sys.exit(1)

        data = load_cards(cards_file())
        print(f"Fetching recent AC submissions for {username}...")
        count, new = sync_leetcode(username, data)
        if count > 0:
            save_cards(cards_file(), data)
            for c in new:
                print(f"  + {c['title']} [{c.get('topic', '')}]")
            print(f"\nDone. {count} new problems imported.")
        else:
            print("No new problems in last 24h.")
        return

    if args and args[0] == "notify":
        from srs.notify import notify_due
        notify_due()
        return

    # Launch TUI with optional direct screen target
    cli_target = None
    if args and args[0] in ("add-problem", "add-concept", "review"):
        cli_target = args[0]

    app = CramApp(cli_target=cli_target)
    app.run()


if __name__ == "__main__":
    main()
