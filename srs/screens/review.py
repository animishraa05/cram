"""Review screen — show due cards, pick one, read note, rate via dialog."""

from __future__ import annotations

import os
from typing import TYPE_CHECKING

from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical
from textual.screen import Screen
from textual.widgets import Label, ListItem, ListView, Markdown, Static

from srs import cards, config
from srs.editor import find_editor, is_vim_family

if TYPE_CHECKING:
    from srs.app import CramApp


class ReviewScreen(Screen):
    """Review screen with split pane layout."""

    ESCAPE_TO_MINIMIZE = False

    BINDINGS = [
        ("j", "cursor_down", "Down"),
        ("k", "cursor_up", "Up"),
        ("o", "open_and_rate", "Review"),
        ("n", "skip_card", "Skip"),
        ("escape", "go_back", "Back"),
    ]

    CSS = """
    #review-container {
        height: 1fr;
    }
    #review-split {
        height: 1fr;
    }
    #review-title {
        text-style: bold;
        color: $foreground;
        padding: 0 1;
        margin-left: 2;
        width: 100%;
        border-bottom: solid $primary;
    }
    #review-list-pane {
        width: 1fr;
        min-width: 20;
        padding: 0 1;
    }
    #review-list {
        border: solid $panel;
        height: 1fr;
    }
    #review-preview-pane {
        width: 1fr;
        min-width: 20;
        border-left: solid $panel;
        padding: 0 1;
    }
    #review-preview-header {
        text-style: bold;
        color: $foreground;
        padding: 0 1;
        margin-bottom: 1;
        width: 100%;
        border-bottom: solid $primary;
    }
    #review-preview-content {
        overflow-y: auto;
        height: 1fr;
    }
    #review-preview-footer {
        color: $text-muted;
        padding: 1 0 0 0;
        width: 100%;
        border-top: solid $panel;
        margin-top: 1;
    }
    #review-status {
        color: $text-muted;
        padding: 1 0 0 2;
        width: 100%;
    }
    #review-footer {
        color: $text-muted;
        padding: 0 0 0 2;
        dock: bottom;
        width: 100%;
    }
    """

    def compose(self) -> ComposeResult:
        with Vertical(id="review-container"):
            yield Static("  Review Due", id="review-title")
            with Horizontal(id="review-split"):
                with Vertical(id="review-list-pane"):
                    yield ListView(id="review-list")
                with Vertical(id="review-preview-pane"):
                    yield Markdown("", id="review-preview-content")
                    yield Static("", id="review-preview-footer")
            yield Static("", id="review-status")
        yield Static(
            "  j/k: navigate  o/Enter: open & review  n: skip  Esc: back",
            id="review-footer",
        )

    def on_mount(self) -> None:
        self._due: list[dict] = []
        self._selected_card: dict | None = None
        self._populate_due()
        self.query_one("#review-preview-pane", Vertical).border_title = " preview "

    def _populate_due(self) -> None:
        data = cards.load_cards(config.cards_file())
        self._due = cards.get_due_cards(data)
        self._selected_card = None
        try:
            due_pane = self.query_one("#review-list-pane", Vertical)
            due_pane.border_title = f" due ({len(self._due)} cards) "
        except Exception:
            pass

        if not self._due:
            all_cards = []
            for key in ("problem_cards", "concept_cards"):
                all_cards.extend(data.get(key, []))

            if all_cards:
                from datetime import datetime, timezone

                now = datetime.now(timezone.utc)
                future = []
                for c in all_cards:
                    try:
                        nr = datetime.fromisoformat(c.get("next_review", "").replace("Z", "+00:00"))
                        if nr > now:
                            future.append(nr)
                    except Exception:
                        pass

                if future:
                    next_up = min(future)
                    delta = next_up - now
                    hours = int(delta.total_seconds() // 3600)
                    if hours < 1:
                        msg = "  No cards due now. Next review in less than an hour."
                    elif hours < 24:
                        msg = f"  No cards due now. Next review in {hours}h."
                    else:
                        days = hours // 24
                        msg = f"  No cards due now. Next review in {days}d."
                else:
                    msg = "  No cards due for review! Great work."
            else:
                msg = "  No cards yet. Add a problem or concept to get started."

            self.query_one("#review-status", Static).update(msg)
            # Clear preview pane when nothing is due
            self.query_one("#review-preview-content", Markdown).update("")
            self.query_one("#review-preview-footer", Static).update("")
            self.query_one("#review-preview-pane", Vertical).border_title = " preview "
            return

        items = []
        for c in self._due:
            topic = c.get("topic", "")
            card_type = c.get("type", "")
            label = c.get("title", "Unknown")
            if topic:
                label += f" [{topic}]"
            if card_type == "concept":
                label = f"(concept) {label}"
            items.append(ListItem(Label(label)))

        lv = self.query_one("#review-list", ListView)
        lv.clear()
        for item in items:
            lv.append(item)
        if self._due:
            lv.index = 0
            lv.focus()
            # Load preview for first card
            self._load_preview(self._due[0])

    def _load_preview(self, card: dict) -> None:
        """Load the note preview into the right pane without opening rating dialog."""
        vault = config.vault()
        folder = card.get("folder") or config.problem_folder()
        filename = card.get("filename", "")
        if not filename:
            from srs.templates import sanitize_filename

            filename = sanitize_filename(card.get("title", "untitled")) + ".md"
        filepath = vault / folder / filename

        topic = card.get("topic", "")
        title = card.get("title", "Unknown")
        label = f" preview: {title} "
        if topic:
            label = f" preview: {title} [{topic}] "
        self.query_one("#review-preview-pane", Vertical).border_title = label

        if filepath.exists():
            try:
                text = filepath.read_text(encoding="utf-8")
            except (OSError, UnicodeDecodeError) as e:
                text = f"(error reading file: {e})"
            preview = text[:800] + ("..." if len(text) > 800 else "")
            self.query_one("#review-preview-content", Markdown).update(preview)
        else:
            self.query_one("#review-preview-content", Markdown).update("  (note file not found)")

        # Calculate and display retrievability (probability of recall)
        from srs.cards import current_retrievability

        prob = current_retrievability(card)
        footer = self.query_one("#review-preview-footer", Static)
        footer.update(f"  Recall Probability: {prob:.1f}%")

        self.query_one("#review-status", Static).update(
            "  Press o/Enter to open note and start review."
        )

    def action_cursor_down(self) -> None:
        self.query_one("#review-list", ListView).action_cursor_down()

    def action_cursor_up(self) -> None:
        self.query_one("#review-list", ListView).action_cursor_up()

    def on_list_view_highlighted(self, event: ListView.Highlighted) -> None:
        """Update preview when cursor moves — do NOT open rating dialog."""
        idx = event.list_view.index
        if idx is None or idx >= len(self._due):
            return
        card = self._due[idx]
        self._selected_card = card
        self._load_preview(card)

    def on_list_view_selected(self, event: ListView.Selected) -> None:
        """Enter key on a list item — same as pressing o: open editor then rate."""
        self.action_open_and_rate()

    def action_open_and_rate(self) -> None:
        """Open the note in the editor so you can read it, then prompt for a rating."""
        lv = self.query_one("#review-list", ListView)
        idx = lv.index
        if idx is None or idx >= len(self._due):
            self.query_one("#review-status", Static).update("  Select a card first.")
            return

        card = self._due[idx]
        self._rating_card_id = card.get("id")
        self.app.call_later(self._do_open_editor, card)

    def _do_open_editor(self, card: dict) -> None:
        """Open the note file in the configured editor, then show the rating dialog."""
        vault = config.vault()
        folder = card.get("folder") or config.problem_folder()
        filename = card.get("filename", "")
        if not filename:
            from srs.templates import sanitize_filename

            filename = sanitize_filename(card.get("title", "untitled")) + ".md"

        notes_dir = vault / folder
        notes_dir.mkdir(parents=True, exist_ok=True)
        filepath = notes_dir / filename

        # Create the note file from template if it doesn't exist yet
        if not filepath.exists():
            card_type = card.get("type", "problem")
            try:
                if card_type == "concept":
                    from srs.templates import concept_template

                    filepath.write_text(
                        concept_template(
                            card.get("title", "Untitled"),
                            card.get("subject", ""),
                        ),
                        encoding="utf-8",
                    )
                else:
                    from srs.templates import problem_template

                    filepath.write_text(
                        problem_template(
                            card.get("title", "Untitled"),
                            card.get("link", ""),
                            card.get("topic", ""),
                        ),
                        encoding="utf-8",
                    )
            except OSError as e:
                self.notify(f"Failed to create note file: {e}", severity="error")
                return

        self.query_one("#review-status", Static).update(f"  Opening: {filepath.name} — review it, then rate.")

        if config.editor_mode() == "embedded":
            from srs.screens.editor import EditorScreen

            def on_editor_done(saved: bool | None) -> None:
                # Refresh preview after editor closes
                try:
                    text = filepath.read_text(encoding="utf-8")
                except (OSError, UnicodeDecodeError):
                    text = ""
                preview = text[:800] + ("..." if len(text) > 800 else "")
                self.query_one("#review-preview-content", Markdown).update(preview)
                self.query_one("#review-status", Static).update("  Rate your recall:")
                from srs.screens.rating_dialog import RatingDialog

                self.app.push_screen(
                    RatingDialog(card, config.desired_retention()),
                    self._on_rate_result,
                )

            self.app.push_screen(EditorScreen(filepath), on_editor_done)
            return

        # External editor path
        editor = find_editor()
        if not editor:
            self.notify("No editor found. Set $EDITOR or install nvim/vi.", severity="error")
            self.query_one("#review-status", Static).update("  Rate your recall (no editor):")
            from srs.screens.rating_dialog import RatingDialog

            self.app.push_screen(
                RatingDialog(card, config.desired_retention()),
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

        # Refresh preview after external editor closes
        try:
            text = filepath.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            text = ""
        preview = text[:800] + ("..." if len(text) > 800 else "")
        self.query_one("#review-preview-content", Markdown).update(preview)
        self.query_one("#review-status", Static).update("  Rate your recall:")
        from srs.screens.rating_dialog import RatingDialog

        self.app.push_screen(
            RatingDialog(card, config.desired_retention()),
            self._on_rate_result,
        )

    def _on_rate_result(self, grade: int | None) -> None:
        if grade is None:
            self.query_one("#review-status", Static).update("  Rating cancelled.")
            self.query_one("#review-list", ListView).focus()
            return

        data = cards.load_cards(config.cards_file())
        card_id = getattr(self, "_rating_card_id", None)
        if not card_id:
            return

        target = cards.find_card_by_id(data, card_id)
        if target:
            cards.update_card(target, grade, config.desired_retention())
            cards.save_cards(config.cards_file(), data)
            self.notify(f"Rated {target.get('title', 'Unknown')}: grade={grade}")
            cram_app: CramApp = self.app  # type: ignore[assignment]
            cram_app.sync_git_background()

        self._populate_due()
        if not self._due:
            self.app.pop_screen()

    def action_skip_card(self) -> None:
        if not self._due:
            return
        self.query_one("#review-status", Static).update("  Skipped.")
        lv = self.query_one("#review-list", ListView)
        idx = lv.index
        if idx is not None and idx < len(self._due):
            self._due.pop(idx)
            items = []
            for c in self._due:
                topic = c.get("topic", "")
                card_type = c.get("type", "")
                label = c.get("title", "Unknown")
                if topic:
                    label += f" [{topic}]"
                if card_type == "concept":
                    label = f"(concept) {label}"
                items.append(ListItem(Label(label)))
            lv.clear()
            for item in items:
                lv.append(item)
            if self._due:
                new_idx = min(idx, len(self._due) - 1)
                lv.index = new_idx
                lv.focus()
                self._load_preview(self._due[new_idx])
            else:
                self.app.pop_screen()

    def action_go_back(self) -> None:
        self.app.pop_screen()
