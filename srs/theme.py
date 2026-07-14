"""Theme system for cram TUI — hex color themes."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class Theme:
    primary: str      # Title bars, active indicators, cursor
    secondary: str    # Status text, descriptions
    border: str       # Preview borders, column dividers
    accent: str       # Selected items, filter match
    muted: str        # Inactive items, status bar
    more_muted: str   # Dimmed descriptions
    text: str         # Normal list item titles
    sub_text: str     # Normal list item descriptions


THEMES: dict[str, Theme] = {
    "default": Theme(
        primary="#3333cc", secondary="#626262", border="#3a3a3a", accent="#9933ff",
        muted="#585858", more_muted="#262626", text="#d0d0d0", sub_text="#808080",
    ),
    "gruvbox": Theme(
        primary="#ff9900", secondary="#767676", border="#993333", accent="#cc3333",
        muted="#993333", more_muted="#303030", text="#ffcc99", sub_text="#808080",
    ),
    "nord": Theme(
        primary="#6699cc", secondary="#669999", border="#666699", accent="#6699ff",
        muted="#336666", more_muted="#666699", text="#ccccff", sub_text="#666699",
    ),
    "tokyonight": Theme(
        primary="#6699ff", secondary="#6699cc", border="#6699ff", accent="#9966ff",
        muted="#666699", more_muted="#303030", text="#ccccff", sub_text="#666699",
    ),
    "dracula": Theme(
        primary="#cc6699", secondary="#9966ff", border="#ff3366", accent="#99ccff",
        muted="#ff3366", more_muted="#303030", text="#eeeeee", sub_text="#949494",
    ),
    "catppuccin": Theme(
        primary="#6699cc", secondary="#cc9966", border="#444444", accent="#99cc66",
        muted="#8a8a8a", more_muted="#303030", text="#eeeeee", sub_text="#a8a8a8",
    ),
    "solarized": Theme(
        primary="#996600", secondary="#009999", border="#996600", accent="#cc3300",
        muted="#993300", more_muted="#336666", text="#e4e4e4", sub_text="#949494",
    ),
    "forest": Theme(
        primary="#339933", secondary="#669966", border="#333300", accent="#cc9933",
        muted="#663300", more_muted="#333300", text="#dadada", sub_text="#949494",
    ),
}


def get_theme(name: str) -> Theme:
    return THEMES.get(name, THEMES["tokyonight"])


def theme_names() -> list[str]:
    return list(THEMES.keys())
