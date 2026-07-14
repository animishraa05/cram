"""Desktop notifications via dunstify for due reviews."""

import subprocess
from pathlib import Path

from srs import cards, config


def send_notification(summary: str, body: str, urgency: str = "normal", timeout: int = 0) -> None:
    cmd = [
        "dunstify",
        "-a", "cram",
        "-u", urgency,
        "-t", str(timeout),
        "-h", "string:x-dunst-stack-tag:cram",
        "-h", "int:value:0",
        summary,
        body,
    ]
    subprocess.run(cmd, check=False)


def notify_due() -> None:
    cfg = config.load_config()
    max_items = int(cfg.get("MAX_ITEMS", "8"))
    urgency = cfg.get("URGENCY", "normal")
    timeout = int(cfg.get("TIMEOUT", "0"))

    data = cards.load_cards(config.cards_file())
    due = cards.get_due_cards(data)

    if not due:
        return

    lines = []
    shown = 0
    for c in due:
        if shown >= max_items:
            break
        card_type = c.get("type", "problem")
        topic = c.get("topic", "")
        suffix = f" [{topic}]" if topic else ""
        lines.append(f"  {c['title']}{suffix}")
        shown += 1

    remaining = len(due) - shown
    if remaining > 0:
        lines.append(f"  ... and {remaining} more")

    problems = [c for c in due if c.get("type") == "problem"]
    concepts = [c for c in due if c.get("type") == "concept"]

    if problems and concepts:
        summary = f"{len(due)} reviews due ({len(problems)} problems, {len(concepts)} concepts)"
    elif problems:
        summary = f"{len(problems)} problem reviews due"
    else:
        summary = f"{len(concepts)} concept reviews due"

    send_notification(summary, "\n".join(lines), urgency, timeout)


if __name__ == "__main__":
    notify_due()
