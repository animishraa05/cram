"""cram main application — Textual TUI with CLI argument support."""

from __future__ import annotations

import sys

from textual.app import App

from srs.config import is_configured, theme_name
from srs.screens.add_concept import AddConceptScreen
from srs.screens.add_problem import AddProblemScreen
from srs.screens.browse import BrowseScreen
from srs.screens.confirm import ConfirmScreen
from srs.screens.home import HomeScreen
from srs.screens.review import ReviewScreen
from srs.screens.settings import SettingsScreen
from srs.screens.setup import SetupScreen
from srs.theme import THEMES


class CramApp(App):
    TITLE = "cram"
    SUB_TITLE = "spaced repetition for problems & concepts"
    CSS_PATH = "cram.tcss"

    SCREENS = {
        "home": HomeScreen,
        "add-problem": AddProblemScreen,
        "add-concept": AddConceptScreen,
        "review": ReviewScreen,
        "browse": BrowseScreen,
        "setup": SetupScreen,
        "settings": SettingsScreen,
    }

    BINDINGS = [
        ("q", "quit", "Quit"),
    ]

    def __init__(self, cli_target: str | None = None) -> None:
        super().__init__()
        self._cli_target = cli_target

    def action_quit(self) -> None:
        self.push_screen(ConfirmScreen("Quit cram?"), self._on_quit_confirm)

    def _on_quit_confirm(self, result: bool | None) -> None:
        if result:
            self.exit()

    def on_mount(self) -> None:
        self._register_themes()
        if not is_configured():
            self.push_screen("setup")
        elif self._cli_target:
            self.push_screen(self._cli_target)
        else:
            self.push_screen("home")

    def on_ready(self) -> None:
        from srs.config import notify_enabled, notify_interval

        if notify_enabled():
            interval = notify_interval()
            self.set_interval(interval, self._periodic_notify, name="due-notifier")

    def _periodic_notify(self) -> None:
        self.run_worker(self._notify_worker, thread=True, exclusive=True, name="notify")

    def _notify_worker(self) -> None:
        from srs.notify import notify_due_silent

        notify_due_silent()

    def _register_themes(self) -> None:
        from textual.theme import Theme as TTheme

        for name, t in THEMES.items():
            textual_theme = TTheme(
                name=f"cram-{name}",
                primary=t.primary,
                secondary=t.secondary,
                accent=t.accent,
                panel=t.border,
                foreground=t.text,
                surface=t.surface,
                background=t.background,
                error=t.error,
                warning=t.warning,
                success=t.success,
            )
            self.register_theme(textual_theme)
        self.theme = f"cram-{theme_name()}"


HELP_TEXT = """\
cram - spaced repetition for problems & concepts

Usage: cram [command]

Commands:
  (no command)            Open TUI home screen
  add-problem             Open problem picker
  add-concept             Open concept form
  review                  Open review queue
  browse                  Browse all cards
  sync                    Fetch last-24h LeetCode submissions
  sync-concepts           Import concepts from Obsidian vault
  export                  Export cards as CSV to stdout
  import FILE             Import cards from Anki TSV export
  notify                  Send dunst notification for due cards
  setup-notifications     Enable hourly dunst notifications (systemd timer)
  remove-notifications    Disable hourly notifications

Options:
  --help, -h              Show this help message
  --version, -v           Show version"""


def main() -> None:
    import logging

    logging.basicConfig(
        level=logging.WARNING,
        format="%(name)s %(levelname)s: %(message)s",
    )

    args = sys.argv[1:]

    if "--help" in args or "-h" in args:
        print(HELP_TEXT)
        sys.exit(0)

    if "--version" in args or "-v" in args:
        from importlib.metadata import PackageNotFoundError, version

        try:
            print(f"cram {version('cram')}")
        except PackageNotFoundError:
            print("cram 0.0.0")
        sys.exit(0)

    # Handle non-TUI subcommands
    if args and args[0] == "sync":
        from srs.cards import load_cards, save_cards
        from srs.config import cards_file, leetcode_username
        from srs.leetcode import LeetCodeAPIError, sync_leetcode

        username = leetcode_username()
        if not username:
            print("Error: LEETCODE_USERNAME not set in ~/.config/cram/config", file=sys.stderr)
            sys.exit(1)

        data = load_cards(cards_file())
        print(f"Fetching recent AC submissions for {username}...")
        try:
            count, new = sync_leetcode(username, data)
        except LeetCodeAPIError as e:
            print(f"Error: {e}", file=sys.stderr)
            sys.exit(1)
        if count > 0:
            save_cards(cards_file(), data)
            for c in new:
                print(f"  + {c.get('title', 'Unknown')} [{c.get('topic', '')}]")
            print(f"\nDone. {count} new problems imported.")
        else:
            print("No new problems in last 24h.")
        return

    if args and args[0] == "notify":
        from srs.notify import notify_due

        notify_due()
        return

    if args and args[0] == "export":
        from srs.export import export_csv

        export_csv()
        return

    if args and args[0] == "import" and len(args) > 1:
        from srs.export import import_anki

        count = import_anki(args[1])
        print(f"Imported {count} new cards from {args[1]}")
        return

    if args and args[0] == "sync-concepts":
        from srs.cards import load_cards, save_cards
        from srs.config import cards_file
        from srs.config import vault as vault_fn
        from srs.obsidian import sync_concepts_from_vault

        data = load_cards(cards_file())
        count, new = sync_concepts_from_vault(vault_fn(), "", data)
        if count > 0:
            save_cards(cards_file(), data)
            for c in new:
                print(f"  + {c.get('title', 'Unknown')}")
            print(f"\nDone. {count} new concepts imported.")
        else:
            print("No new concept notes found in vault.")
        return

    if args and args[0] == "setup-notifications":
        from srs.notifications import setup_notifications

        msg = setup_notifications()
        print(msg)
        return

    if args and args[0] == "remove-notifications":
        from srs.notifications import remove_notifications

        msg = remove_notifications()
        print(msg)
        return

    # Launch TUI with optional direct screen target
    cli_target = None
    if args and args[0] in ("add-problem", "add-concept", "review", "browse"):
        cli_target = args[0]

    app = CramApp(cli_target=cli_target)
    app.run()
