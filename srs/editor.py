"""Editor detection — find the best available text editor."""

from __future__ import annotations

import os
import shutil


def find_editor() -> str | None:
    """Find the best available editor.

    Resolution order: $VISUAL > $EDITOR > nvim > vim > vi
    Returns the command name, or None if no editor found.
    """
    for var in ("VISUAL", "EDITOR"):
        editor = os.environ.get(var, "").strip()
        if editor:
            return editor

    for cmd in ("nvim", "vim", "vi"):
        if shutil.which(cmd):
            return cmd

    return None


def is_vim_family(editor: str) -> bool:
    """Check if an editor is vim/nvim (supports vim-specific args)."""
    base = editor.split()[-1] if "/" in editor else editor
    return base in ("nvim", "vim", "vi")
