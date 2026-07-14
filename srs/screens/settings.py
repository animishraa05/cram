"""Settings screen — theme selector + config display."""

from __future__ import annotations

from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical
from textual.screen import Screen
from textual.widgets import Static

from srs import config
from srs.theme import THEMES, get_theme


class SettingsScreen(Screen):
    """Settings overlay: palette preview + config + theme selector."""

    ESCAPE_TO_MINIMIZE = False

    def compose(self) -> ComposeResult:
        with Vertical(id="settings-overlay"):
            yield Static("cram Settings", id="settings-title", classes="col-title")
            with Horizontal(id="settings-columns"):
                yield Vertical(id="palette-col")
                yield Vertical(id="config-col")
                yield Vertical(id="theme-col")
            yield Static("tab: switch  s: save  enter: confirm  esc: cancel", id="settings-footer")

    def on_mount(self) -> None:
        self._selected_idx = 0
        self._active_tab = "theme"
        self._current_theme = config.theme_name()
        self._new_theme = self._current_theme
        self._build_palette()
        self._build_config()
        self._build_theme_list()

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
            swatch = Static(f"   ", classes="swatch-row")
            swatch.styles.background = color
            swatch.styles.color = color
            label = Static(f" {name}")
            col.mount(swatch)
            col.mount(label)

    def _build_config(self) -> None:
        col = self.query_one("#config-col", Vertical)
        col.remove_children()

        col.mount(Static("Config", classes="col-title"))

        cfg_path = config.config_path()
        col.mount(Static(f" {cfg_path}", classes="theme-item"))
        col.mount(Static("", classes="theme-item"))

        vault_path = config.vault()
        col.mount(Static(f" Vault: {vault_path}", classes="theme-item"))

        problem_folder = config.problem_folder()
        col.mount(Static(f" Problems: {problem_folder}", classes="theme-item"))

        username = config.leetcode_username()
        col.mount(Static(f" LeetCode: {username or '(not set)'}", classes="theme-item"))

        retention = config.desired_retention()
        col.mount(Static(f" Retention: {retention}", classes="theme-item"))

    def _build_theme_list(self) -> None:
        col = self.query_one("#theme-col", Vertical)
        col.remove_children()

        col.mount(Static("Theme", classes="col-title"))

        for name in THEMES.keys():
            if name == self._new_theme:
                item = Static(f"● {name}", classes="theme-item theme-item-active")
            else:
                item = Static(f"  {name}", classes="theme-item")
            col.mount(item)

    def key_down(self) -> None:
        themes = list(THEMES.keys())
        self._selected_idx = min(self._selected_idx + 1, len(themes) - 1)
        self._new_theme = themes[self._selected_idx]
        self._build_palette()
        self._build_theme_list()

    def key_up(self) -> None:
        themes = list(THEMES.keys())
        self._selected_idx = max(self._selected_idx - 1, 0)
        self._new_theme = themes[self._selected_idx]
        self._build_palette()
        self._build_theme_list()

    def _apply_theme(self) -> None:
        from textual.theme import Theme as TTheme

        t = get_theme(self._new_theme)
        textual_theme = TTheme(
            name=f"cram-{self._new_theme}",
            primary=t.primary,
            secondary=t.secondary,
            accent=t.accent,
            panel=t.border,
        )
        self.app.register_theme(textual_theme)
        self.app.theme = f"cram-{self._new_theme}"

    def key_s(self) -> None:
        from srs.config import save_config, load_config

        cfg = load_config()
        cfg["THEME"] = self._new_theme
        save_config(cfg)
        self._apply_theme()
        self.notify(f"Theme saved: {self._new_theme}")

    def key_enter(self) -> None:
        from srs.config import save_config, load_config

        cfg = load_config()
        cfg["THEME"] = self._new_theme
        save_config(cfg)
        self._apply_theme()
        self.app.pop_screen()

    def key_escape(self) -> None:
        self.app.pop_screen()
