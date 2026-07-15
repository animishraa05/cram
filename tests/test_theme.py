"""Tests for srs.theme — theme system."""

from srs.theme import THEMES, Theme, get_theme, theme_names


def test_all_themes_have_required_fields():
    for name, theme in THEMES.items():
        assert isinstance(theme, Theme), f"{name} is not a Theme"
        assert theme.primary, f"{name} missing primary"
        assert theme.secondary, f"{name} missing secondary"
        assert theme.border, f"{name} missing border"
        assert theme.accent, f"{name} missing accent"
        assert theme.muted, f"{name} missing muted"
        assert theme.more_muted, f"{name} missing more_muted"
        assert theme.text, f"{name} missing text"
        assert theme.sub_text, f"{name} missing sub_text"


def test_theme_count():
    assert len(THEMES) == 8


def test_theme_names():
    names = theme_names()
    assert len(names) == 8
    assert "tokyonight" in names
    assert "dracula" in names
    assert "gruvbox" in names
    assert "nord" in names
    assert "catppuccin" in names
    assert "solarized" in names
    assert "forest" in names
    assert "default" in names


def test_get_theme_valid():
    theme = get_theme("tokyonight")
    assert theme.primary == "#7aa2f7"
    assert theme.accent == "#7dcfff"


def test_get_theme_unknown_returns_tokyonight():
    theme = get_theme("nonexistent_theme")
    assert theme.primary == "#7aa2f7"  # tokyonight primary


def test_theme_colors_are_strings():
    for name, theme in THEMES.items():
        assert isinstance(theme.primary, str), f"{name}.primary not string"
        assert isinstance(theme.text, str), f"{name}.text not string"


def test_all_themes_unique():
    names = list(THEMES.keys())
    assert len(names) == len(set(names)), "Duplicate theme names"
