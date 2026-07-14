"""Add Concept screen — ask subject, ask title, open nvim, rate."""

from __future__ import annotations

import subprocess
import shutil

from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical
from textual.screen import Screen
from textual.widgets import Input, Label, Static

from srs import cards, config
from srs.screens.rating import Rating


class AddConceptScreen(Screen):
    """Add Concept screen with form and preview."""

    ESCAPE_TO_MINIMIZE = False

    def compose(self) -> ComposeResult:
        with Vertical(id="concept-container"):
            yield Static("  Add Concept", id="concept-title")
            with Horizontal(id="concept-split"):
                with Vertical(id="concept-form-pane"):
                    yield Label("Subject (e.g. Networking, DBMS, OS):")
                    yield Input(placeholder="Subject", id="subject-input")
                    yield Label("Concept title:")
                    yield Input(placeholder="Title", id="title-input")
                with Vertical(id="concept-preview-pane"):
                    yield Static("Note Preview", id="concept-preview-header")
                    yield Static("", id="concept-preview-content")
                    yield Static("", id="concept-preview-footer")
            yield Static("", id="concept-status")
            yield Rating()

    def on_mount(self) -> None:
        self.query_one(Rating).display = False
        self.query_one("#title-input", Input).display = False
        self.query_one("#concept-status", Static).update("  Enter subject, then press Enter.")
        self.query_one("#subject-input", Input).focus()

    def on_input_submitted(self, event: Input.Submitted) -> None:
        if event.input.id == "subject-input":
            subject = event.value.strip()
            if not subject:
                return
            vault = config.vault()
            subject_folder = vault / subject
            if not subject_folder.exists():
                subject_folder.mkdir(parents=True, exist_ok=True)
                self.query_one("#concept-status", Static).update(
                    f"  Created new subject folder: {subject}/"
                )
            else:
                self.query_one("#concept-status", Static).update(
                    f"  Using existing folder: {subject}/"
                )
            self.query_one("#subject-input", Input).display = False
            self.query_one("#title-input", Input).display = True
            self.query_one("#title-input", Input).focus()

        elif event.input.id == "title-input":
            title = event.value.strip()
            if not title:
                return
            self._open_nvim(title)

    def _open_nvim(self, title: str) -> None:
        from srs.templates import concept_template, sanitize_filename

        subject = self.query_one("#subject-input", Input).value.strip()
        vault = config.vault()
        notes_dir = vault / subject
        notes_dir.mkdir(parents=True, exist_ok=True)

        filename = sanitize_filename(title) + ".md"
        filepath = notes_dir / filename

        if not filepath.exists():
            filepath.write_text(concept_template(title, subject))

        text = filepath.read_text()
        preview = text[:800] + ("..." if len(text) > 800 else "")
        self.query_one("#concept-preview-content", Static).update(preview)
        self.query_one("#concept-preview-header", Static).update(f"  {filepath.name}")
        self.query_one("#concept-status", Static).update(f"  Opening nvim: {filepath.name}")

        if not shutil.which("nvim"):
            self.notify("nvim not found in PATH. Install neovim first.", severity="error")
            self.query_one(Rating).display = True
            self.query_one("#concept-status", Static).update("  Rate your recall (nvim unavailable):")
            return

        self.app.suspend()
        try:
            subprocess.run(["nvim", "+normal G$", "+startinsert", str(filepath)])
        finally:
            self.app.resume()

        text = filepath.read_text()
        preview = text[:800] + ("..." if len(text) > 800 else "")
        self.query_one("#concept-preview-content", Static).update(preview)
        self.query_one(Rating).display = True
        self.query_one("#concept-status", Static).update("  Rate your recall:")

    def key_1(self) -> None:
        if self.query_one(Rating).display:
            self.post_message(Rating.Rated(1))

    def key_2(self) -> None:
        if self.query_one(Rating).display:
            self.post_message(Rating.Rated(2))

    def key_3(self) -> None:
        if self.query_one(Rating).display:
            self.post_message(Rating.Rated(3))

    def key_4(self) -> None:
        if self.query_one(Rating).display:
            self.post_message(Rating.Rated(4))

    def key_escape(self) -> None:
        self.app.pop_screen()

    def on_rating_rated(self, event: Rating.Rated) -> None:
        subject = self.query_one("#subject-input", Input).value.strip()
        title = self.query_one("#title-input", Input).value.strip()
        vault = config.vault()
        from srs.templates import sanitize_filename as _sanitize
        filename = _sanitize(title) + ".md"

        data = cards.load_cards(config.cards_file())
        existing = cards.find_card_by_title(data, title, "concept")

        if existing:
            cards.update_card(existing, event.grade, config.desired_retention())
        else:
            folder = str((vault / subject).relative_to(vault))
            new_card = cards.make_card(
                "concept",
                title,
                subject=subject,
                folder=folder,
                filename=filename,
            )
            cards.update_card(new_card, event.grade, config.desired_retention())
            data.setdefault("concept_cards", []).append(new_card)

        cards.save_cards(config.cards_file(), data)
        self.notify(f"Rated {title}: grade={event.grade}")
        self.app.pop_screen()
