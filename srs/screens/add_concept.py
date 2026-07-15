"""Add Concept screen — ask subject, ask title, open nvim, rate."""

from __future__ import annotations

import os
from typing import TYPE_CHECKING

from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical
from textual.screen import Screen
from textual.widgets import Input, Label, Markdown, Static

from srs import cards, config
from srs.editor import find_editor, is_vim_family

if TYPE_CHECKING:
    from srs.app import CramApp


class AddConceptScreen(Screen):
    """Add Concept screen with form and preview."""

    ESCAPE_TO_MINIMIZE = False

    BINDINGS = [
        ("escape", "go_back", "Back"),
    ]

    CSS = """
    #concept-container { height: 1fr; }
    #concept-split { height: 1fr; }
    #concept-title {
        text-style: bold;
        color: $foreground;
        padding: 0 1;
        margin-left: 2;
        width: 100%;
        border-bottom: solid $primary;
    }
    #concept-form-pane {
        width: 1fr;
        min-width: 20;
        padding: 1 2;
    }
    #concept-form-pane Label { text-style: bold; margin-top: 1; }
    #concept-form-pane Input { margin-bottom: 1; }
    #concept-preview-pane {
        width: 1fr;
        min-width: 20;
        border-left: solid $panel;
        padding: 0 1;
    }
    #concept-preview-header {
        text-style: bold; color: $foreground;
        padding: 0 1; margin-bottom: 1; width: 100%;
        border-bottom: solid $primary;
    }
    #concept-preview-content { overflow-y: auto; height: 1fr; }
    #concept-preview-footer {
        color: $text-muted; padding: 1 0 0 0;
        width: 100%; border-top: solid $panel; margin-top: 1;
    }
    #concept-status { color: $text-muted; padding: 1 0 0 2; width: 100%; }
    #concept-footer {
        color: $text-muted;
        padding: 0 0 0 2;
        dock: bottom;
        width: 100%;
    }
    """

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
                    yield Markdown("", id="concept-preview-content")
                    yield Static("", id="concept-preview-footer")
            yield Static("", id="concept-status")
        yield Static(
            "  Enter: advance  Esc: back",
            id="concept-footer",
        )

    def on_mount(self) -> None:
        self.query_one("#title-input", Input).display = False
        self.query_one("#concept-status", Static).update("  Enter subject, then press Enter.")
        self.query_one("#subject-input", Input).focus()
        self.query_one("#concept-preview-pane", Vertical).border_title = " preview "
        self.query_one("#concept-form-pane", Vertical).border_title = " form "

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
            self._title = title
            self.app.call_later(self._do_open_editor, title)

    def _do_open_editor(self, title: str) -> None:

        from srs.templates import concept_template, sanitize_filename

        subject = self.query_one("#subject-input", Input).value.strip()
        vault = config.vault()
        notes_dir = vault / subject
        notes_dir.mkdir(parents=True, exist_ok=True)

        filename = sanitize_filename(title) + ".md"
        filepath = notes_dir / filename

        if not filepath.exists():
            try:
                filepath.write_text(concept_template(title, subject), encoding="utf-8")
            except OSError as e:
                self.notify(f"Failed to create file: {e}", severity="error")
                return

        try:
            text = filepath.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError) as e:
            text = f"(error reading file: {e})"
        preview = text[:800] + ("..." if len(text) > 800 else "")
        self.query_one("#concept-preview-content", Markdown).update(preview)
        self.query_one("#concept-preview-header", Static).update(f"  {filepath.name}")
        self.query_one("#concept-status", Static).update(f"  Opening editor: {filepath.name}")

        data = cards.load_cards(config.cards_file())
        existing = cards.find_card_by_title(data, title, "concept")
        if not existing:
            existing = cards.make_card(
                "concept", title, subject=subject, folder=subject, filename=filename
            )

        editor = find_editor()
        if config.editor_mode() == "embedded":
            from srs.screens.editor import EditorScreen

            def on_editor_done(saved: bool | None) -> None:
                if not saved:
                    self.query_one("#concept-status", Static).update("  Editor cancelled.")
                    return
                try:
                    text = filepath.read_text(encoding="utf-8")
                except (OSError, UnicodeDecodeError) as e:
                    text = f"(error reading file: {e})"
                preview = text[:800] + ("..." if len(text) > 800 else "")
                self.query_one("#concept-preview-content", Markdown).update(preview)
                self.query_one(
                    "#concept-preview-pane", Vertical
                ).border_title = f" preview: {filename} "
                self.query_one("#concept-status", Static).update("  Rate your recall:")

                from srs.screens.rating_dialog import RatingDialog

                # Fetch target concept card (might need to load cards first)
                data_c = cards.load_cards(config.cards_file())
                existing_c = cards.find_card_by_title(data_c, title, "concept")
                if not existing_c:
                    existing_c = cards.make_card(
                        "concept",
                        title,
                        subject=subject,
                        folder=subject,
                        filename=filename,
                    )
                self.app.push_screen(
                    RatingDialog(existing_c, config.desired_retention()),
                    self._on_rate_result,
                )

            self.app.push_screen(EditorScreen(filepath), on_editor_done)
            return

        editor = find_editor()
        if not editor:
            self.notify("No editor found. Set $EDITOR or install nvim/vi.", severity="error")
            self.query_one("#concept-status", Static).update("  Rate your recall (no editor):")
            from srs.screens.rating_dialog import RatingDialog

            self.app.push_screen(
                RatingDialog(existing, config.desired_retention()),
                self._on_rate_result,
            )
            return

        args = [editor]
        if is_vim_family(editor):
            args += ["+normal G$", "+startinsert"]
        args.append(str(filepath))

        with self.app.suspend():
            pid = os.fork()
            if pid < 0:
                self.notify("Failed to fork process", severity="error")
                return
            if pid == 0:
                try:
                    os.execvp(editor, args)
                except OSError:
                    os._exit(1)
            else:
                os.waitpid(pid, 0)

        try:
            text = filepath.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError) as e:
            text = f"(error reading file: {e})"
        preview = text[:800] + ("..." if len(text) > 800 else "")
        self.query_one("#concept-preview-content", Markdown).update(preview)
        self.query_one("#concept-preview-pane", Vertical).border_title = f" preview: {filename} "
        self.query_one("#concept-status", Static).update("  Rate your recall:")
        from srs.screens.rating_dialog import RatingDialog

        data = cards.load_cards(config.cards_file())
        existing = cards.find_card_by_title(data, title, "concept")
        if not existing:
            existing = cards.make_card(
                "concept", title, subject=subject, folder=subject, filename=filename
            )

        self.app.push_screen(
            RatingDialog(existing, config.desired_retention()),
            self._on_rate_result,
        )

    def action_go_back(self) -> None:
        if self.query_one("#title-input", Input).display:
            self.query_one("#title-input", Input).display = False
            self.query_one("#subject-input", Input).display = True
            self.query_one("#subject-input", Input).focus()
            self.query_one("#concept-status", Static).update("  Enter subject, then press Enter.")
        else:
            self.app.pop_screen()

    def _on_rate_result(self, grade: int | None) -> None:
        if grade is None:
            self.app.pop_screen()
            return

        subject = self.query_one("#subject-input", Input).value.strip()
        title = getattr(self, "_title", self.query_one("#title-input", Input).value.strip())
        vault = config.vault()
        from srs.templates import sanitize_filename as _sanitize

        filename = _sanitize(title) + ".md"

        subject_folder = (vault / subject).resolve()
        if not str(subject_folder).startswith(str(vault.resolve())):
            self.notify("Invalid subject path", severity="error")
            self.app.pop_screen()
            return

        data = cards.load_cards(config.cards_file())
        existing = cards.find_card_by_title(data, title, "concept")

        if existing:
            cards.update_card(existing, grade, config.desired_retention())
        else:
            folder = str(subject_folder.relative_to(vault.resolve()))
            new_card = cards.make_card(
                "concept",
                title,
                subject=subject,
                folder=folder,
                filename=filename,
            )
            cards.update_card(new_card, grade, config.desired_retention())
            data.setdefault("concept_cards", []).append(new_card)

        cards.save_cards(config.cards_file(), data)
        self.notify(f"Rated {title}: grade={grade}")
        cram_app: CramApp = self.app  # type: ignore[assignment]
        cram_app.sync_git_background()
        self.app.pop_screen()
