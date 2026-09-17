"""Settings screen — theme selector + editable config display."""

from __future__ import annotations

from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical, VerticalScroll
from textual.screen import Screen
from textual.widgets import Input, Label, ListItem, ListView, Static, Switch

from srs import config
from srs.theme import THEMES, get_theme


class SettingsScreen(Screen):
    """Settings overlay: palette preview + config + theme selector."""

    ESCAPE_TO_MINIMIZE = False

    BINDINGS = [
        ("ctrl+h", "focus_left", "Focus Config"),
        ("ctrl+l", "focus_right", "Focus Theme"),
        ("ctrl+s", "save_settings", "Save"),
        ("escape", "go_back", "Back"),
    ]

    def compose(self) -> ComposeResult:
        with Vertical(id="settings-overlay"):
            yield Static("cram Settings", id="settings-title", classes="col-title")
            with Horizontal(id="settings-columns"):
                with VerticalScroll(id="config-col"):
                    yield Static("Config", classes="col-title")
                    yield Label("Vault:")
                    yield Input(placeholder="vault path", id="vault-input")
                    yield Label("Problem Folder:")
                    yield Input(placeholder="folder", id="folder-input")
                    yield Label("LeetCode Username:")
                    yield Input(placeholder="username", id="leetcode-input")
                    yield Label("Retention (0.0-1.0):")
                    yield Input(placeholder="0.9", id="retention-input")
                    yield Label("Notifications (Space to toggle):")
                    yield Switch(id="notify-switch", animate=False)
                    yield Label("Notify Interval (seconds):")
                    yield Input(placeholder="3600", id="interval-input")
                    yield Label("Editor Command (e.g. nvim, vim, code):")
                    yield Input(placeholder="nvim", id="editor-cmd-input")
                    yield Label("Editor Mode (external/embedded):")
                    yield Input(placeholder="embedded", id="editor-mode-input")
                with Vertical(id="right-col"):
                    with Vertical(id="theme-col"):
                        yield Static("Theme Selection", classes="col-title")
                        yield ListView(id="theme-list")
                    yield Vertical(id="palette-col")
            yield Static(
                "ctrl+h: config  ctrl+l: themes  j/k: select theme  ctrl+s: save  Esc: back",
                id="settings-footer",
            )


    def on_mount(self) -> None:
        self._selected_idx = 0
        self._current_theme = config.theme_name()
        self._new_theme = self._current_theme
        self._build_palette()
        self._build_config_values()
        self._build_theme_list()
        self.query_one("#vault-input", Input).focus()

    def _build_palette(self) -> None:
        col = self.query_one("#palette-col", Vertical)
        col.remove_children()

        col.mount(Static("Palette", classes="col-title"))

        theme = get_theme(self._new_theme)
        colors = [
            ("Primary", theme.primary),
            ("Secondary", theme.secondary),
            ("Accent", theme.accent),
            ("Border", theme.border),
            ("Muted", theme.muted),
            ("Text", theme.text),
            ("SubText", theme.sub_text),
        ]

        for name, color in colors:
            swatch = Static("   ", classes="swatch-row")
            swatch.styles.background = color
            swatch.styles.color = color
            label = Static(f" {name}")
            col.mount(swatch)
            col.mount(label)

    def _build_config_values(self) -> None:
        # Show the raw configured vault path, not the computed fallback
        raw_vault = config.get("OBSIDIAN_VAULT", "")
        self.query_one("#vault-input", Input).value = raw_vault
        self.query_one("#folder-input", Input).value = config.problem_folder()
        self.query_one("#leetcode-input", Input).value = config.leetcode_username() or ""
        self.query_one("#retention-input", Input).value = str(config.desired_retention())
        self.query_one("#notify-switch", Switch).value = config.notify_enabled()
        self.query_one("#interval-input", Input).value = str(config.notify_interval())
        self.query_one("#editor-cmd-input", Input).value = config.preferred_editor()
        self.query_one("#editor-mode-input", Input).value = config.editor_mode()

    def _build_theme_list(self) -> None:
        theme_list = self.query_one("#theme-list", ListView)
        theme_list.clear()

        themes = list(THEMES.keys())
        for name in themes:
            theme_list.append(ListItem(Label(name), id=f"theme-{name}"))

        if self._new_theme in themes:
            idx = themes.index(self._new_theme)
            theme_list.index = idx
            self._selected_idx = idx

    def on_list_view_highlighted(self, event: ListView.Highlighted) -> None:
        if event.list_view.id == "theme-list" and event.item is not None:
            themes = list(THEMES.keys())
            idx = event.list_view.index
            if idx is not None and 0 <= idx < len(themes):
                self._selected_idx = idx
                self._new_theme = themes[idx]
                self._build_palette()

    def action_focus_left(self) -> None:
        self.query_one("#vault-input", Input).focus()

    def action_focus_right(self) -> None:
        self.query_one("#theme-list", ListView).focus()

    def action_go_back(self) -> None:
        self.app.pop_screen()

    def action_save_settings(self) -> None:
        from srs.config import invalidate_cache, save_config

        notify_on = self.query_one("#notify-switch", Switch).value
        cfg = {
            "OBSIDIAN_VAULT": self.query_one("#vault-input", Input).value.strip(),
            "PROBLEM_FOLDER": self.query_one("#folder-input", Input).value.strip(),
            "LEETCODE_USERNAME": self.query_one("#leetcode-input", Input).value.strip(),
            "DESIRED_RETENTION": self.query_one("#retention-input", Input).value.strip(),
            "NOTIFY_ENABLED": "true" if notify_on else "false",
            "NOTIFY_INTERVAL": self.query_one("#interval-input", Input).value.strip(),
            "EDITOR": self.query_one("#editor-cmd-input", Input).value.strip(),
            "EDITOR_MODE": self.query_one("#editor-mode-input", Input).value.strip(),
            "THEME": self._new_theme,
            "CARDS_FILE": str(config.cards_file()),
        }
        save_config(cfg)
        invalidate_cache()

        # Update systemd user timer based on the toggle state
        try:
            from srs.notifications import remove_notifications, setup_notifications
            if notify_on:
                setup_notifications()
            else:
                remove_notifications()
        except Exception:
            pass

        self.notify("Settings saved")
        self.app.theme = f"cram-{self._new_theme}"
        self.app.pop_screen()
