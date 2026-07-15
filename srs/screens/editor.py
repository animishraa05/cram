"""Editor utilities — find and launch external editors."""

from __future__ import annotations

import os


def find_editor() -> str | None:
    """Find an available editor: $EDITOR, then try nvim, vim, vi."""
    editor = os.environ.get("EDITOR", "")
    if editor:
        return editor.split()[0]
    for name in ("nvim", "vim", "vi"):
        if os.path.which(name):
            return name
    return None


def is_vim_family(editor: str) -> bool:
    """Check if editor is vim-family (nvim, vim, vi)."""
    basename = os.path.basename(editor)
    return basename in ("nvim", "vim", "vi")
