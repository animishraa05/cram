"""Git Auto-Sync utility to commit and push notes and card changes."""

from __future__ import annotations

import subprocess
import threading
from collections.abc import Callable
from pathlib import Path


def is_git_repo(path: Path) -> bool:
    try:
        res = subprocess.run(
            ["git", "rev-parse", "--is-inside-work-tree"],
            cwd=path,
            capture_output=True,
            text=True,
            check=False,
            timeout=5,
        )
        return res.returncode == 0
    except Exception:
        return False


def has_git_remote(path: Path) -> bool:
    try:
        res = subprocess.run(
            ["git", "remote"],
            cwd=path,
            capture_output=True,
            text=True,
            check=False,
            timeout=5,
        )
        return bool(res.stdout.strip())
    except Exception:
        return False


def run_git_sync(path: Path) -> str:
    """Runs git add, commit, and push. Returns status message."""
    if not is_git_repo(path):
        return f"Not a git repo: {path.name}"

    try:
        # Add files
        subprocess.run(["git", "add", "."], cwd=path, check=True, timeout=15)

        # Check if changes exist to commit
        diff = subprocess.run(
            ["git", "diff", "--cached", "--quiet"],
            cwd=path,
            check=False,
            timeout=10,
        )
        if diff.returncode == 0:
            return f"No changes in {path.name}"

        # Commit
        subprocess.run(
            ["git", "commit", "-m", "cram auto-sync: update reviews and notes"],
            cwd=path,
            check=True,
            timeout=15,
        )

        # Push if remote exists
        if has_git_remote(path):
            subprocess.run(["git", "push"], cwd=path, check=True, timeout=30)
            return f"Sync complete for {path.name} (pushed)"
        return f"Sync complete for {path.name} (local commit)"
    except Exception as e:
        return f"Sync failed for {path.name}: {e}"


def sync_all_background(
    vault_path: Path, cards_file_path: Path, callback: Callable[[str], None] | None = None
) -> None:
    def worker():
        results = []
        # 1. Sync vault
        if is_git_repo(vault_path):
            res_v = run_git_sync(vault_path)
            results.append(res_v)

        # 2. Sync cards folder if different and is a git repo
        cards_dir = cards_file_path.parent
        if cards_dir.resolve() != vault_path.resolve() and is_git_repo(cards_dir):
            res_c = run_git_sync(cards_dir)
            results.append(res_c)

        if callback and results:
            callback("; ".join(results))

    thread = threading.Thread(target=worker, daemon=True)
    thread.start()
