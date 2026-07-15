"""Desktop notifications via dunstify for due reviews."""

import shutil
import subprocess
import sys
from datetime import datetime, timedelta, timezone

from srs import cards, config

_notifier_path: str | None = None


def _has_dunstify() -> bool:
    global _notifier_path
    if _notifier_path is None:
        _notifier_path = shutil.which("dunstify") or shutil.which("notify-send")
    return _notifier_path is not None


def send_notification(summary: str, body: str, urgency: str = "normal", timeout: int = 0) -> None:
    dunstify = shutil.which("dunstify")
    if dunstify:
        cmd = [
            "dunstify",
            "-a",
            "cram",
            "-u",
            urgency,
            "-t",
            str(timeout),
            "-h",
            "string:x-dunst-stack-tag:cram",
            "-h",
            "int:value:0",
            summary,
            body,
        ]
    else:
        cmd = [
            "notify-send",
            "-u",
            urgency,
            "-t",
            str(timeout if timeout > 0 else 5000),
            summary,
            body,
        ]
    subprocess.run(cmd, check=False, timeout=10)


def _build_notification() -> tuple[str, str] | None:
    """Build notification summary and body from due cards.

    Returns (summary, body) or None if no cards due.
    """
    data = cards.load_cards(config.cards_file())
    due = cards.get_due_cards(data)

    if not due:
        return None

    now = datetime.now(timezone.utc)
    overdue_cutoff = now - timedelta(days=1)

    problems = [c for c in due if c.get("type") == "problem"]
    concepts = [c for c in due if c.get("type") == "concept"]

    overdue = []
    for c in due:
        nr_str = c.get("next_review")
        if not nr_str:
            continue
        try:
            nr = datetime.fromisoformat(nr_str.replace("Z", "+00:00"))
            if nr < overdue_cutoff:
                overdue.append(c)
        except (ValueError, TypeError):
            pass

    parts = [f"{len(due)} due"]
    if problems:
        parts.append(f"{len(problems)} problem{'s' if len(problems) != 1 else ''}")
    if concepts:
        parts.append(f"{len(concepts)} concept{'s' if len(concepts) != 1 else ''}")
    if overdue:
        parts.append(f"{len(overdue)} overdue")
    summary = " \u00b7 ".join(parts)

    cfg = config.load_config()
    try:
        max_items = int(cfg.get("MAX_ITEMS", "8"))
    except ValueError:
        max_items = 8

    lines = []
    shown = 0
    for c in due:
        if shown >= max_items:
            break
        tag = "[P]" if c.get("type") == "problem" else "[C]"
        topic = c.get("topic", "")
        suffix = f" ({topic})" if topic else ""
        lines.append(f"  {tag} {c.get('title', 'Unknown')}{suffix}")
        shown += 1

    remaining = len(due) - shown
    if remaining > 0:
        lines.append(f"  ...and {remaining} more")

    return summary, "\n".join(lines)


def notify_due() -> None:
    """Send dunst notification for due cards. Prints to stdout (CLI mode)."""
    if not _has_dunstify():
        print(
            "Warning: neither dunstify nor notify-send found. "
            "Install dunst or libnotify-bin for notifications.",
            file=sys.stderr,
        )
        return

    result = _build_notification()
    if result is None:
        print("No cards due.")
        return

    summary, body = result
    cfg = config.load_config()
    urgency = cfg.get("URGENCY", "normal")
    try:
        timeout = int(cfg.get("TIMEOUT", "0"))
    except ValueError:
        timeout = 0

    send_notification(summary, body, urgency, timeout)
    print(f"Notified: {summary}")


def notify_due_silent() -> str | None:
    """Send dunst notification for due cards. Silent (no stdout).

    Returns the summary string if notification was sent, None otherwise.
    Safe to call from the TUI.
    """
    if not _has_dunstify():
        return None

    result = _build_notification()
    if result is None:
        return None

    summary, body = result
    cfg = config.load_config()
    urgency = cfg.get("URGENCY", "normal")
    try:
        timeout = int(cfg.get("TIMEOUT", "0"))
    except ValueError:
        timeout = 0

    send_notification(summary, body, urgency, timeout)
    return summary


if __name__ == "__main__":
    notify_due()
