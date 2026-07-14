"""Add Problem screen — list last-24h LeetCode problems, pick one, nvim, rate."""

from __future__ import annotations

import subprocess
import shutil
from pathlib import Path

from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical
from textual.screen import Screen
from textual.widgets import Input, Label, ListItem, ListView, Static

from srs import cards, config
from srs.screens.rating import Rating


class CreateProblem(Screen):
    """Create a new problem note manually."""

    ESCAPE_TO_MINIMIZE = False

    def compose(self) -> ComposeResult:
        with Vertical(id="create-container"):
            yield Static("  Create Problem", id="create-title")
            with Vertical(id="create-form"):
                yield Label("Title:")
                yield Input(placeholder="Two Sum", id="title-input")
                yield Label("Link (optional):")
                yield Input(placeholder="https://leetcode.com/two-sum/", id="link-input")
                yield Label("Topic (optional):")
                yield Input(placeholder="Array", id="topic-input")
            yield Static("", id="create-status")
            yield Rating()

    def on_mount(self) -> None:
        self.query_one(Rating).display = False
        self._card = None
        self.query_one("#title-input", Input).focus()

    def on_input_submitted(self, event: Input.Submitted) -> None:
        if event.input.id == "title-input":
            title = event.input.value.strip()
            if not title:
                self.query_one("#create-status", Static).update("Title is required!")
                return
            self.query_one("#link-input", Input).focus()

        elif event.input.id == "link-input":
            self.query_one("#topic-input", Input).focus()

        elif event.input.id == "topic-input":
            self._create_card()

    def _create_card(self) -> None:
        title = self.query_one("#title-input", Input).value.strip()
        link = self.query_one("#link-input", Input).value.strip()
        topic = self.query_one("#topic-input", Input).value.strip()

        if not title:
            self.query_one("#create-status", Static).update("Title is required!")
            return

        from srs.cards import make_card

        data = cards.load_cards(config.cards_file())
        card = make_card("problem", title, link=link, topic=topic)
        data.setdefault("problem_cards", []).append(card)
        cards.save_cards(config.cards_file(), data)

        self.query_one("#create-status", Static).update(f"Created: {title}")
        self._open_nvim(card, data)

    def _open_nvim(self, card: dict, data: dict) -> None:
        from srs.templates import problem_template, sanitize_filename

        vault = config.vault()
        folder = config.problem_folder()
        notes_dir = vault / folder
        notes_dir.mkdir(parents=True, exist_ok=True)

        filename = sanitize_filename(card["title"]) + ".md"
        filepath = notes_dir / filename

        if not filepath.exists():
            filepath.write_text(
                problem_template(
                    card["title"],
                    card.get("link", ""),
                    card.get("topic", ""),
                )
            )

        card["folder"] = folder
        card["filename"] = filename
        cards.save_cards(config.cards_file(), data)
        self._card = card

        self.query_one("#create-status", Static).update(f"Opening nvim: {filepath.name}")

        if not shutil.which("nvim"):
            self.notify("nvim not found in PATH. Install neovim first.", severity="error")
            self.query_one(Rating).display = True
            self.query_one("#create-status", Static).update("Rate your recall (nvim unavailable):")
            return

        self.app.suspend()
        try:
            subprocess.run(["nvim", "+normal G$", "+startinsert", str(filepath)])
        finally:
            self.app.resume()

        self.query_one("#create-status", Static).update("Rate your recall:")
        self.query_one(Rating).display = True
        self.query_one(Input, "input").display = False

    def on_rating_rated(self, event: Rating.Rated) -> None:
        if not self._card:
            self.app.pop_screen()
            return

        data = cards.load_cards(config.cards_file())
        target = None
        for c in data.get("problem_cards", []):
            if c.get("id") == self._card.get("id"):
                target = c
                break

        if target:
            cards.update_card(target, event.grade, config.desired_retention())
            cards.save_cards(config.cards_file(), data)
            self.notify(f"Rated {target['title']}: grade={event.grade}")

        self.app.pop_screen()

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


class AddProblemScreen(Screen):
    """Add Problem screen with split pane layout."""

    ESCAPE_TO_MINIMIZE = False

    def compose(self) -> ComposeResult:
        with Vertical(id="problem-container"):
            yield Static("  Add Problem", id="problem-title")
            with Horizontal(id="problem-split"):
                with Vertical(id="problem-list-pane"):
                    yield ListView(id="problem-list")
                with Vertical(id="problem-preview-pane"):
                    yield Static("Note Preview", id="problem-preview-header")
                    yield Static("", id="problem-preview-content")
                    yield Static("", id="problem-preview-footer")
            yield Static("", id="problem-status")
            yield Rating()

    def on_mount(self) -> None:
        self.query_one(Rating).display = False
        self._populate_problems()

    def _populate_problems(self) -> None:
        data = cards.load_cards(config.cards_file())
        folder = Path(config.problem_folder())
        vault = config.vault()

        unsynced = []
        for c in data.get("problem_cards", []):
            f = c.get("filename")
            if f and (vault / folder / f).exists():
                continue
            unsynced.append(c)

        items = [ListItem(Label("[+] Create new problem..."))]
        for c in unsynced:
            topic = c.get("topic", "")
            title = c.get("title", "Unknown")
            items.append(ListItem(Label(f"{title} [{topic}]")))

        lv = self.query_one("#problem-list", ListView)
        lv.clear()
        for item in items:
            lv.append(item)
        self._problems = unsynced

        if not unsynced:
            self.query_one("#problem-status", Static).update(
                "  No unsolved problems. Run 'cram sync' or create a new one."
            )

    def on_list_view_selected(self, event: ListView.Selected) -> None:
        idx = event.index
        if idx == 0:
            self.app.push_screen(CreateProblem())
            return

        if idx - 1 >= len(getattr(self, "_problems", [])):
            return
        card = self._problems[idx - 1]
        self._open_nvim(card)

    def _open_nvim(self, card: dict) -> None:
        from srs.templates import problem_template, sanitize_filename

        vault = config.vault()
        folder = config.problem_folder()
        notes_dir = vault / folder
        notes_dir.mkdir(parents=True, exist_ok=True)

        filename = sanitize_filename(card["title"]) + ".md"
        filepath = notes_dir / filename

        if not filepath.exists():
            filepath.write_text(
                problem_template(
                    card["title"],
                    card.get("link", ""),
                    card.get("topic", ""),
                )
            )

        card["folder"] = folder
        card["filename"] = filename

        text = filepath.read_text()
        preview = text[:800] + ("..." if len(text) > 800 else "")
        self.query_one("#problem-preview-content", Static).update(preview)
        self.query_one("#problem-preview-header", Static).update(f"  {filepath.name}")
        self.query_one("#problem-status", Static).update(f"  Opening nvim: {filepath.name}")

        if not shutil.which("nvim"):
            self.notify("nvim not found in PATH. Install neovim first.", severity="error")
            self.query_one(Rating).display = True
            self.query_one("#problem-status", Static).update("  Rate your recall (nvim unavailable):")
            return

        self.app.suspend()
        try:
            subprocess.run(["nvim", "+normal G$", "+startinsert", str(filepath)])
        finally:
            self.app.resume()

        text = filepath.read_text()
        preview = text[:800] + ("..." if len(text) > 800 else "")
        self.query_one("#problem-preview-content", Static).update(preview)
        self.query_one(Rating).display = True
        self.query_one("#problem-status", Static).update("  Rate your recall:")

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
        data = cards.load_cards(config.cards_file())

        idx = self.query_one("#problem-list").index
        if idx == 0 or idx - 1 >= len(self._problems):
            return

        card_id = self._problems[idx - 1].get("id")
        target = None
        for c in data.get("problem_cards", []):
            if c.get("id") == card_id:
                target = c
                break

        if target:
            cards.update_card(target, event.grade, config.desired_retention())
            cards.save_cards(config.cards_file(), data)
            self.notify(f"Rated {target['title']}: grade={event.grade}")

        self.app.pop_screen()
