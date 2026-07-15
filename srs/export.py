"""Export and import card data."""

from __future__ import annotations

import csv
import sys
from pathlib import Path

from srs import cards
from srs.config import cards_file as _cards_file


def export_csv(path: Path | None = None) -> None:
    """Export all cards to CSV on stdout or file."""
    data = cards.load_cards(_cards_file() if path is None else path)
    all_cards = []
    for key in ("problem_cards", "concept_cards"):
        all_cards.extend(data.get(key, []))

    writer = csv.writer(sys.stdout)
    writer.writerow(
        ["type", "title", "topic", "link", "subject", "review_count", "interval", "next_review"]
    )
    for c in all_cards:
        writer.writerow(
            [
                c.get("type", ""),
                c.get("title", ""),
                c.get("topic", ""),
                c.get("link", ""),
                c.get("subject", ""),
                c.get("review_count", 0),
                c.get("interval", 1),
                c.get("next_review", ""),
            ]
        )


def import_anki(file_path: str) -> int:
    """Import cards from a tab-separated Anki export file.

    Expects lines like: front<TAB>back<TAB>tags
    Returns number of cards imported.
    """
    from srs.config import cards_file

    try:
        fh = open(file_path, encoding="utf-8")
    except (FileNotFoundError, OSError) as e:
        print(f"Error: {e}", file=sys.stderr)
        return 0

    data = cards.load_cards(cards_file())
    count = 0

    with fh:
        for line in fh:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            parts = line.split("\t")
            if len(parts) < 2:
                continue

            title = parts[0].strip()
            tags = parts[2].strip() if len(parts) > 2 else ""
            topic = tags.split()[0] if tags else "General"

            existing = cards.find_card_by_title(data, title, "problem")
            if existing:
                continue

            card = cards.make_card("problem", title, topic=topic)
            data.setdefault("problem_cards", []).append(card)
            count += 1

    if count > 0:
        cards.save_cards(cards_file(), data)
    return count
