"""Editor detection — find the best available text editor."""

from __future__ import annotations

import os
import shutil


def find_editor() -> str | None:
    """Find the best available editor.

    Resolution order:
      1. EDITOR key in ~/.config/cram/config (set during setup)
      2. $VISUAL environment variable
      3. $EDITOR environment variable
      4. nvim → vim → vi (auto-detect)

    Returns the command name, or None if no editor found.
    """
    from srs.config import preferred_editor

    configured = preferred_editor().strip()
    if configured:
        return configured

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
