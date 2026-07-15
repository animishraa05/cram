"""Obsidian vault scanner — import concepts from markdown files with frontmatter."""

from __future__ import annotations

import re
from pathlib import Path


def scan_vault_for_concepts(vault: Path, folder: str = "") -> list[dict]:
    """Scan vault for markdown files with type: concept in frontmatter.

    Returns list of dicts with title, subject, filename, path.
    """
    search_dir = vault / folder if folder else vault
    if not search_dir.exists():
        return []

    results = []
    for md_file in search_dir.rglob("*.md"):
        try:
            text = md_file.read_text(encoding="utf-8")
        except OSError:
            continue

        frontmatter_match = re.match(r"^---\r?\n(.*?)\r?\n---", text, re.DOTALL)
        if not frontmatter_match:
            continue

        fm = frontmatter_match.group(1)
        if not re.search(r"^type:\s*concept\s*$", fm, re.MULTILINE):
            continue

        title = ""
        subject = ""
        for line in fm.splitlines():
            line = line.strip()
            if ":" in line:
                key, _, val = line.partition(":")
                key = key.strip().lower()
                val = val.strip().strip('"').strip("'")
                if key == "title":
                    title = val
                elif key == "subject":
                    subject = val

        if not title:
            title = md_file.stem

        try:
            rel = md_file.relative_to(vault)
            folder_str = str(rel.parent) if str(rel.parent) != "." else ""
        except ValueError:
            folder_str = ""

        results.append(
            {
                "title": title,
                "subject": subject,
                "filename": md_file.name,
                "folder": folder_str,
                "path": str(md_file),
            }
        )

    return results


def sync_concepts_from_vault(vault: Path, folder: str, cards_data: dict) -> tuple[int, list[dict]]:
    """Import concept notes from vault as concept cards.

    Returns (new_count, new_cards_list).
    """
    from srs.cards import find_card_by_title, make_card

    notes = scan_vault_for_concepts(vault, folder)
    new_cards: list[dict] = []

    for note in notes:
        existing = find_card_by_title(cards_data, note["title"], "concept")
        if existing:
            continue

        card = make_card(
            "concept",
            note["title"],
            subject=note.get("subject", ""),
            folder=note.get("folder", ""),
            filename=note.get("filename", ""),
        )
        cards_data.setdefault("concept_cards", []).append(card)
        new_cards.append(card)

    return len(new_cards), new_cards
