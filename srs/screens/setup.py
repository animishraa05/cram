"""First-run setup wizard — guides new users through initial configuration."""

from __future__ import annotations

from pathlib import Path

from textual.app import ComposeResult
from textual.containers import Vertical
from textual.screen import Screen
from textual.widgets import Header, Input, Label, Static

from srs import config


class SetupScreen(Screen):
    """First-run setup: vault path, problem folder, LeetCode username, theme."""

    CSS = """
    #setup-container {
        width: 70;
        max-width: 90%;
        padding: 2 3;
        background: $surface;
    }
    #setup-container Label {
        text-style: bold;
        margin-top: 1;
    }
    #setup-container Input {
        margin-bottom: 1;
    }
    #setup-status {
        color: $text-muted;
        margin-top: 1;
    }
    #setup-welcome {
        text-style: bold;
        margin-bottom: 1;
    }
    #setup-step {
        color: $text-muted;
        margin-bottom: 1;
    }
    """

    def compose(self) -> ComposeResult:
        yield Header()
        with Vertical(id="setup-container"):
            yield Static("Welcome to cram!", id="setup-welcome")
            yield Static("Step 1 of 4: Obsidian Vault", id="setup-step")
            yield Label("Path to your Obsidian vault (required):")
            yield Input(placeholder="/home/user/vault", id="vault-input")
            yield Label("Problem folder (press Enter for default):", id="folder-label")
            yield Input(placeholder="Private/Daily/Problems", id="folder-input")
            yield Label("LeetCode username (optional, press Enter to skip):", id="leetcode-label")
            yield Input(placeholder="username", id="leetcode-input")
            yield Label("Theme (tokyonight, dracula, gruvbox, nord, catppuccin, solarized, forest, default):", id="theme-label")
            yield Input(placeholder="tokyonight", id="theme-input")
            yield Static("", id="setup-status")

    def on_mount(self) -> None:
        self._step = 0
        self._cfg: dict[str, str] = {}
        self.query_one("#folder-label", Label).display = False
        self.query_one("#folder-input", Input).display = False
        self.query_one("#leetcode-label", Label).display = False
        self.query_one("#leetcode-input", Input).display = False
        self.query_one("#theme-label", Label).display = False
        self.query_one("#theme-input", Input).display = False
        self.query_one("#vault-input", Input).focus()

    def on_input_submitted(self, event: Input.Submitted) -> None:
        if event.input.id == "vault-input":
            self._handle_vault()
        elif event.input.id == "folder-input":
            self._handle_folder()
        elif event.input.id == "leetcode-input":
            self._handle_leetcode()
        elif event.input.id == "theme-input":
            self._handle_theme()

    def _handle_vault(self) -> None:
        vault_path = self.query_one("#vault-input", Input).value.strip()
        if not vault_path:
            self.query_one("#setup-status", Static).update("Vault path is required!")
            return

        vault = Path(vault_path).expanduser().resolve()
        if not vault.exists():
            vault.mkdir(parents=True, exist_ok=True)
            self.query_one("#setup-status", Static).update(f"Created: {vault}")
        else:
            self.query_one("#setup-status", Static).update(f"Using: {vault}")

        self._cfg["OBSIDIAN_VAULT"] = str(vault)
        self._step = 1

        self.query_one("#setup-step", Static).update("Step 2 of 4: Problem Folder")
        self.query_one("#vault-input", Input).display = False
        self.query_one(Label).display = False  # hide vault label
        self.query_one("#folder-label", Label).display = True
        self.query_one("#folder-input", Input).display = True
        self.query_one("#folder-input", Input).focus()

    def _handle_folder(self) -> None:
        folder = self.query_one("#folder-input", Input).value.strip()
        if not folder:
            folder = "Private/Daily/Problems"

        self._cfg["PROBLEM_FOLDER"] = folder
        self._step = 2

        self.query_one("#setup-step", Static).update("Step 3 of 4: LeetCode Username")
        self.query_one("#folder-input", Input).display = False
        self.query_one("#folder-label", Label).display = False
        self.query_one("#leetcode-label", Label).display = True
        self.query_one("#leetcode-input", Input).display = True
        self.query_one("#leetcode-input", Input).focus()

    def _handle_leetcode(self) -> None:
        username = self.query_one("#leetcode-input", Input).value.strip()
        if username:
            self._cfg["LEETCODE_USERNAME"] = username
        self._step = 3

        self.query_one("#setup-step", Static).update("Step 4 of 4: Theme")
        self.query_one("#leetcode-input", Input).display = False
        self.query_one("#leetcode-label", Label).display = False
        self.query_one("#theme-label", Label).display = True
        self.query_one("#theme-input", Input).display = True
        self.query_one("#theme-input", Input).focus()

    def _handle_theme(self) -> None:
        from srs.theme import theme_names

        theme = self.query_one("#theme-input", Input).value.strip().lower()
        if theme not in theme_names():
            theme = "tokyonight"
        self._cfg["THEME"] = theme

        self._finish_setup()

    def _finish_setup(self) -> None:
        from srs.config import save_config, cards_file

        # Save config
        self._cfg["CARDS_FILE"] = str(cards_file())
        save_config(self._cfg)

        # Create cards.json if needed
        cards_path = cards_file()
        cards_path.parent.mkdir(parents=True, exist_ok=True)
        if not cards_path.exists():
            cards_path.write_text('{"problem_cards": [], "concept_cards": []}')

        self.query_one("#setup-step", Static).update("Setup complete!")
        self.query_one("#setup-status", Static).update(
            f"Config saved to {config.config_path()}\n"
            f"Vault: {self._cfg.get('OBSIDIAN_VAULT', '')}\n"
            f"Theme: {self._cfg.get('THEME', 'tokyonight')}\n\n"
            "Launching cram..."
        )

        self.set_timer(1.5, self._exit_setup)

    def _exit_setup(self) -> None:
        self.app.switch_screen("home")
