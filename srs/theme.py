"""Theme system for cram TUI — hex color themes."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class Theme:
    primary: str  # Title bars, active indicators, cursor
    secondary: str  # Status text, descriptions
    border: str  # Preview borders, column dividers
    accent: str  # Selected items, filter match
    muted: str  # Inactive items, status bar
    more_muted: str  # Dimmed descriptions
    text: str  # Normal list item titles
    sub_text: str  # Normal list item descriptions
    surface: str  # Modal backgrounds, card surfaces
    background: str  # App background (behind screens)
    error: str  # Error buttons, dangerous actions
    warning: str  # Warning buttons, caution
    success: str  # Success buttons, confirmations
    text_muted: str  # Footer hints, secondary text


THEMES: dict[str, Theme] = {
    "catppuccin": Theme(
        primary="#cba6f7",
        secondary="#89b4fa",
        accent="#f5c2e7",
        border="#585b70",
        muted="#585b70",
        more_muted="#313244",
        text="#cdd6f4",
        sub_text="#a6adc8",
        surface="#313244",
        background="#1e1e2e",
        error="#f38ba8",
        warning="#f9e2af",
        success="#a6e3a1",
        text_muted="#6c7086",
    ),
    "tokyonight": Theme(
        primary="#7aa2f7",
        secondary="#bb9af7",
        accent="#7dcfff",
        border="#414868",
        muted="#565f89",
        more_muted="#1f2335",
        text="#c0caf5",
        sub_text="#a9b1d6",
        surface="#1a1b26",
        background="#24283b",
        error="#f7768e",
        warning="#e0af68",
        success="#9ece6a",
        text_muted="#565f89",
    ),
    "dracula": Theme(
        primary="#bd93f9",
        secondary="#ff79c6",
        accent="#8be9fd",
        border="#44475a",
        muted="#6272a4",
        more_muted="#282a36",
        text="#f8f8f2",
        sub_text="#bfbfbf",
        surface="#282a36",
        background="#191a21",
        error="#ff5555",
        warning="#f1fa8c",
        success="#50fa7b",
        text_muted="#6272a4",
    ),
    "nord": Theme(
        primary="#88c0d0",
        secondary="#81a1c1",
        accent="#8fbcbb",
        border="#4c566a",
        muted="#4c566a",
        more_muted="#3b4252",
        text="#eceff4",
        sub_text="#d8dee9",
        surface="#3b4252",
        background="#2e3440",
        error="#bf616a",
        warning="#ebcb8b",
        success="#a3be8c",
        text_muted="#4c566a",
    ),
    "gruvbox": Theme(
        primary="#d79921",
        secondary="#b8bb26",
        accent="#83a598",
        border="#504945",
        muted="#665c54",
        more_muted="#3c3836",
        text="#ebdbb2",
        sub_text="#d5c4a1",
        surface="#282828",
        background="#1d2021",
        error="#fb4934",
        warning="#fabd2f",
        success="#b8bb26",
        text_muted="#928374",
    ),
    "solarized": Theme(
        primary="#268bd2",
        secondary="#2aa198",
        accent="#6c71c4",
        border="#586e75",
        muted="#657b83",
        more_muted="#073642",
        text="#839496",
        sub_text="#93a1a1",
        surface="#002b36",
        background="#001e27",
        error="#dc322f",
        warning="#b58900",
        success="#859900",
        text_muted="#586e75",
    ),
    "forest": Theme(
        primary="#a7c080",
        secondary="#dbbc7f",
        accent="#7fbbb3",
        border="#56635f",
        muted="#56635f",
        more_muted="#3a4544",
        text="#d3c6aa",
        sub_text="#b3b9a8",
        surface="#2d353b",
        background="#273439",
        error="#e67e80",
        warning="#dbbc7f",
        success="#a7c080",
        text_muted="#7a8478",
    ),
    "default": Theme(
        primary="#7c8cf8",
        secondary="#a0a0f0",
        accent="#f090b0",
        border="#3a3f55",
        muted="#5c6078",
        more_muted="#2a2d3e",
        text="#e0e0f0",
        sub_text="#a0a0c0",
        surface="#1e2030",
        background="#141620",
        error="#f06070",
        warning="#f0c060",
        success="#80d080",
        text_muted="#606880",
    ),
}


def get_theme(name: str) -> Theme:
    return THEMES.get(name, THEMES["tokyonight"])


def theme_names() -> list[str]:
    return list(THEMES.keys())
