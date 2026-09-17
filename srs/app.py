"""cram main application — Textual TUI with CLI argument support."""

from __future__ import annotations

import sys

from textual.app import App

from srs.config import is_configured, theme_name
from srs.screens.add_concept import AddConceptScreen
from srs.screens.add_problem import AddProblemScreen
from srs.screens.browse import BrowseScreen
from srs.screens.confirm import ConfirmScreen
from srs.screens.help import HelpScreen
from srs.screens.home import HomeScreen
from srs.screens.review import ReviewScreen
from srs.screens.settings import SettingsScreen
from srs.screens.setup import SetupScreen
from srs.screens.stats import StatsScreen
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
        "stats": StatsScreen,
        "help": HelpScreen,
    }

    BINDINGS = [
        ("q", "quit", "Quit"),
        ("t", "push_screen('stats')", "Stats"),
        ("question_mark", "show_help", "Help"),
    ]

    def __init__(self, cli_target: str | None = None) -> None:
        super().__init__()
        self._cli_target = cli_target

    async def action_quit(self) -> None:  # type: ignore[override]
        self.push_screen(ConfirmScreen("Quit cram?"), self._on_quit_confirm)

    def _on_quit_confirm(self, result: bool | None) -> None:
        if result:
            self.exit()

    def action_show_help(self) -> None:
        self.push_screen(HelpScreen())

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
        from srs.config import notify_enabled
        from srs.notify import notify_due_silent

        if notify_enabled():
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

    def sync_git_background(self) -> None:
        from srs import config
        from srs.git_sync import sync_all_background

        def on_sync_done(msg: str) -> None:
            self.call_from_thread(self.notify, f"Git Backup: {msg}")

        sync_all_background(config.vault(), config.cards_file(), on_sync_done)


def print_help() -> None:
    """Print a rich, fully-formatted help page to the terminal."""
    from importlib.metadata import PackageNotFoundError, version

    from rich.console import Console
    from rich.padding import Padding
    from rich.rule import Rule
    from rich.table import Table
    from rich.text import Text

    try:
        ver = version("cram")
    except PackageNotFoundError:
        ver = "dev"

    console = Console()

    # ── Header ────────────────────────────────────────────────────────
    console.print()
    header = Text()
    header.append("cram", style="bold cyan")
    header.append(f"  v{ver}", style="dim")
    header.append("  —  spaced repetition for problems & concepts", style="")
    console.print(header)
    console.print(Rule(style="dim"))

    # ── Usage ─────────────────────────────────────────────────────────
    console.print(Padding(Text("USAGE", style="bold yellow"), (1, 0, 0, 0)))
    console.print("  [bold]cram[/bold] [dim][[command]] [[options]][/dim]")

    # ── TUI Commands ──────────────────────────────────────────────────
    console.print(Padding(Text("TUI COMMANDS", style="bold yellow"), (1, 0, 0, 0)))
    tui_table = Table(show_header=False, box=None, padding=(0, 2))
    tui_table.add_column(style="bold cyan", no_wrap=True)
    tui_table.add_column(style="")
    tui_commands = [
        ("cram",            "Open the home dashboard (default)"),
        ("cram add-problem", "Open the problem picker / creator"),
        ("cram add-concept", "Open the concept form"),
        ("cram review",     "Jump straight to the review queue"),
        ("cram browse",     "Browse, search, and manage all cards"),
    ]
    for cmd, desc in tui_commands:
        tui_table.add_row(cmd, desc)
    console.print(tui_table)

    # ── CLI Commands ──────────────────────────────────────────────────
    console.print(Padding(Text("CLI COMMANDS", style="bold yellow"), (1, 0, 0, 0)))
    cli_table = Table(show_header=False, box=None, padding=(0, 2))
    cli_table.add_column(style="bold cyan", no_wrap=True)
    cli_table.add_column(style="")
    cli_commands = [
        ("cram sync",                  "Fetch last-24h accepted LeetCode submissions"),
        ("cram sync-concepts",         "Scan vault/notes folder and import concept cards"),
        ("cram export",                "Export all cards as CSV to stdout"),
        ("cram import FILE",           "Import cards from an Anki TSV export file"),
        ("cram notify",                "Send a dunst desktop notification for due cards"),
        ("cram setup-notifications",   "Enable hourly reminders via systemd user timer"),
        ("cram remove-notifications",  "Disable the hourly systemd reminder"),
    ]
    for cmd, desc in cli_commands:
        cli_table.add_row(cmd, desc)
    console.print(cli_table)

    # ── Options ───────────────────────────────────────────────────────
    console.print(Padding(Text("OPTIONS", style="bold yellow"), (1, 0, 0, 0)))
    opt_table = Table(show_header=False, box=None, padding=(0, 2))
    opt_table.add_column(style="bold cyan", no_wrap=True)
    opt_table.add_column(style="")
    opt_table.add_row("--help,    -h", "Show this help message")
    opt_table.add_row("--version, -v", "Print version and exit")
    console.print(opt_table)

    # ── TUI Keybindings ───────────────────────────────────────────────
    console.print(Padding(Text("TUI KEYBINDINGS", style="bold yellow"), (1, 0, 0, 0)))
    key_table = Table(show_header=True, box=None, padding=(0, 2), header_style="dim")
    key_table.add_column("Key", style="bold magenta", no_wrap=True)
    key_table.add_column("Where", style="dim", no_wrap=True)
    key_table.add_column("Action", style="")
    keybindings = [
        ("j / k",     "Anywhere",      "Move cursor down / up"),
        ("o / Enter", "Anywhere",      "Select / confirm"),
        ("Esc",       "Anywhere",      "Go back / cancel"),
        ("q",         "Home",          "Quit (with confirm dialog)"),
        (",",         "Anywhere",      "Open Settings"),
        ("/",         "Browse",        "Focus search box"),
        ("n",         "Review",        "Skip selected card"),
        ("d",         "Browse",        "Delete selected card"),
        ("e",         "Browse",        "Edit topic of selected card"),
        ("a/h/g/e",   "Rating dialog", "Rate: Again / Hard / Good / Easy"),
        ("← →",       "Rating dialog", "Move focus between rating buttons"),
        ("Ctrl+s",    "Settings",      "Save settings"),
        ("Ctrl+s",    "Embedded editor","Save note and close editor"),
        ("Ctrl+h/l",  "Settings",      "Focus config column / theme column"),
    ]
    for key, where, action in keybindings:
        key_table.add_row(key, where, action)
    console.print(key_table)

    # ── Spaced Repetition Ratings ─────────────────────────────────────
    console.print(Padding(Text("REVIEW RATINGS  (FSRS-4.5)", style="bold yellow"), (1, 0, 0, 0)))
    rate_table = Table(show_header=True, box=None, padding=(0, 2), header_style="dim")
    rate_table.add_column("Key", style="bold magenta", no_wrap=True)
    rate_table.add_column("Grade", no_wrap=True)
    rate_table.add_column("Meaning")
    rate_table.add_row("a", "Again", "Complete blackout — couldn't recall at all  (~next: 1d)")
    rate_table.add_row("h", "Hard",  "Significant effort to recall               (~next: 4d)")
    rate_table.add_row("g", "Good",  "Some thought needed, but got it            (~next: 12d)")
    rate_table.add_row("e", "Easy",  "Instant recall, no effort                  (~next: 28d)")
    console.print(rate_table)

    # ── Config ────────────────────────────────────────────────────────
    console.print(Padding(Text("CONFIG FILE", style="bold yellow"), (1, 0, 0, 0)))
    console.print("  [dim]Location:[/dim]  [bold]~/.config/cram/config[/bold]")
    console.print()
    cfg_table = Table(show_header=True, box=None, padding=(0, 2), header_style="dim")
    cfg_table.add_column("Key", style="bold cyan", no_wrap=True)
    cfg_table.add_column("Default", style="green", no_wrap=True)
    cfg_table.add_column("Description")
    cfg_entries = [
        ("OBSIDIAN_VAULT",   "(empty)",  "Path to Obsidian vault — optional, uses local notes dir if unset"),
        ("PROBLEM_FOLDER",  "Private/Daily/Problems", "Sub-folder inside vault for problem notes"),
        ("LEETCODE_USERNAME","(empty)",  "Your LeetCode handle — optional, needed only for sync"),
        ("DESIRED_RETENTION","0.9",      "Target recall probability: 0.85–0.95 (default 0.9)"),
        ("EDITOR_MODE",      "embedded", "'embedded' (built-in TextArea) or 'external' (any editor)"),
        ("EDITOR",           "(auto)",   "Editor command when EDITOR_MODE=external (e.g. nvim, code)"),
        ("THEME",            "tokyonight","Color theme name (see list below)"),
        ("NOTIFY_ENABLED",   "true",     "Enable/disable background due-card reminders"),
        ("NOTIFY_INTERVAL",  "3600",     "Reminder frequency in seconds (minimum 60)"),
        ("CARDS_FILE",       "~/.local/share/cram/cards.json", "Override path for the cards database"),
    ]
    for key, default, desc in cfg_entries:
        cfg_table.add_row(key, default, desc)
    console.print(cfg_table)

    # ── Themes ────────────────────────────────────────────────────────
    console.print(Padding(Text("THEMES", style="bold yellow"), (1, 0, 0, 0)))
    console.print(
        "  [cyan]default[/cyan]  [cyan]dracula[/cyan]  [cyan]gruvbox[/cyan]  "
        "[cyan]nord[/cyan]  [cyan]tokyonight[/cyan]  [cyan]catppuccin[/cyan]  "
        "[cyan]solarized[/cyan]  [cyan]forest[/cyan]"
    )
    console.print("  Change with [bold]cram[/bold] → Settings → Theme Selection [dim](live preview)[/dim]")

    # ── Examples ─────────────────────────────────────────────────────
    console.print(Padding(Text("EXAMPLES", style="bold yellow"), (1, 0, 0, 0)))
    ex_table = Table(show_header=False, box=None, padding=(0, 2))
    ex_table.add_column(style="bold cyan", no_wrap=True)
    ex_table.add_column(style="dim")
    examples = [
        ("cram",                    "# open the TUI home dashboard"),
        ("cram review",             "# jump straight to due-card review"),
        ("cram sync",               "# import today's LeetCode solves"),
        ("cram sync-concepts",      "# import concepts from vault/notes"),
        ("cram export > cards.csv", "# export everything to a CSV file"),
        ("cram import anki.txt",    "# bulk-import from Anki TSV export"),
    ]
    for cmd, comment in examples:
        ex_table.add_row(cmd, comment)
    console.print(ex_table)

    # ── Footer ────────────────────────────────────────────────────────
    console.print(Rule(style="dim"))
    console.print(
        "  [dim]Docs & source:[/dim]  "
        "[bold cyan]https://github.com/animishraa05/cram[/bold cyan]"
    )
    console.print()


def main() -> None:
    import logging

    logging.basicConfig(
        level=logging.WARNING,
        format="%(name)s %(levelname)s: %(message)s",
    )

    args = sys.argv[1:]

    if "--help" in args or "-h" in args:
        print_help()
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
