"""Add Problem screen — list last-24h LeetCode problems, pick one, nvim, rate."""

from __future__ import annotations

from pathlib import Path

from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical
from textual.screen import Screen
from textual.widgets import Input, Label, ListItem, ListView, Markdown, Static

from srs import cards, config
from srs.editor import find_editor, is_vim_family


class CreateProblem(Screen):
    """Create a new problem note manually."""

    ESCAPE_TO_MINIMIZE = False

    BINDINGS = [
        ("escape", "go_back", "Back"),
    ]

    CSS = """
    #create-container { height: 1fr; }
    #create-title {
        text-style: bold;
        color: $foreground;
        padding: 0 1;
        margin-left: 2;
        width: 100%;
        border-bottom: solid $primary;
    }
    #create-form { padding: 1 0; }
    #create-form Label { text-style: bold; margin-top: 1; }
    #create-form Input { margin-bottom: 1; }
    #create-status { color: $text-muted; padding: 1 0 0 2; width: 100%; }
    #create-footer {
        color: $text-muted;
        padding: 0 0 0 2;
        dock: bottom;
        width: 100%;
    }
    """

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
        yield Static(
            "  Enter: advance  Esc: back",
            id="create-footer",
        )

    def on_mount(self) -> None:
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
        self._card = card
        self.app.call_later(self._do_open_editor, card, data)

    def _do_open_editor(self, card: dict, data: dict) -> None:
        import os
        import time

        from srs.templates import problem_template, sanitize_filename

        vault = config.vault()
        folder = config.problem_folder()
        notes_dir = vault / folder
        notes_dir.mkdir(parents=True, exist_ok=True)

        filename = sanitize_filename(card.get("title", "untitled")) + ".md"
        filepath = notes_dir / filename

        if not filepath.exists():
            try:
                filepath.write_text(
                    problem_template(
                        card.get("title", "Untitled"),
                        card.get("link", ""),
                        card.get("topic", ""),
                    ),
                    encoding="utf-8",
                )
            except OSError as e:
                self.notify(f"Failed to create file: {e}", severity="error")
                return

        card["folder"] = folder
        card["filename"] = filename
        cards.save_cards(config.cards_file(), data)

        self.query_one("#create-status", Static).update(f"Opening editor: {filepath.name}")

        editor = find_editor()
        if not editor:
            self.notify("No editor found. Set $EDITOR or install nvim/vi.", severity="error")
            self.query_one("#create-status", Static).update("  Rate your recall (no editor):")
            from srs.screens.rating_dialog import RatingDialog

            self.app.push_screen(
                RatingDialog(self._card, config.desired_retention()),
                self._on_rate_result,
            )
            return

        args = [editor]
        if is_vim_family(editor):
            args += ["+normal G$", "+startinsert"]
        args.append(str(filepath))

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

        time.sleep(0.1)
        self.app.refresh()

        self.query_one("#create-status", Static).update("Rate your recall:")
        from srs.screens.rating_dialog import RatingDialog

        self.app.push_screen(
            RatingDialog(self._card, config.desired_retention()),
            self._on_rate_result,
        )

    def _on_rate_result(self, grade: int | None) -> None:
        if not self._card or grade is None:
            self.app.pop_screen()
            return

        data = cards.load_cards(config.cards_file())
        target = None
        for c in data.get("problem_cards", []):
            if c.get("id") == self._card.get("id"):
                target = c
                break

        if target:
            cards.update_card(target, grade, config.desired_retention())
            cards.save_cards(config.cards_file(), data)
            self.notify(f"Rated {target.get('title', 'Unknown')}: grade={grade}")

        self.app.pop_screen()

    def action_go_back(self) -> None:
        self.app.pop_screen()


class AddProblemScreen(Screen):
    """Add Problem screen with split pane layout."""

    ESCAPE_TO_MINIMIZE = False

    BINDINGS = [
        ("j", "cursor_down", "Down"),
        ("k", "cursor_up", "Up"),
        ("escape", "go_back", "Back"),
    ]

    CSS = """
    #problem-container { height: 1fr; }
    #problem-split { height: 1fr; }
    #problem-title {
        text-style: bold;
        color: $foreground;
        padding: 0 1;
        margin-left: 2;
        width: 100%;
        border-bottom: solid $primary;
    }
    #problem-list-pane { width: 1fr; min-width: 20; padding: 0 1; }
    #problem-list { border: solid $panel; height: 1fr; }
    #problem-preview-pane {
        width: 1fr; min-width: 20;
        border-left: solid $panel; padding: 0 1;
    }
    #problem-preview-header {
        text-style: bold; color: $foreground;
        padding: 0 1; margin-bottom: 1; width: 100%;
        border-bottom: solid $primary;
    }
    #problem-preview-content { overflow-y: auto; height: 1fr; }
    #problem-preview-footer {
        color: $text-muted; padding: 1 0 0 0;
        width: 100%; border-top: solid $panel; margin-top: 1;
    }
    #problem-status { color: $text-muted; padding: 1 0 0 2; width: 100%; }
    #problem-footer {
        color: $text-muted;
        padding: 0 0 0 2;
        dock: bottom;
        width: 100%;
    }
    """

    def compose(self) -> ComposeResult:
        with Vertical(id="problem-container"):
            yield Static("  Add Problem", id="problem-title")
            with Horizontal(id="problem-split"):
                with Vertical(id="problem-list-pane"):
                    yield ListView(id="problem-list")
                with Vertical(id="problem-preview-pane"):
                    yield Markdown("", id="problem-preview-content")
                    yield Static("", id="problem-preview-footer")
            yield Static("", id="problem-status")
        yield Static(
            "  j/k: navigate  o/Enter: select  Esc: back",
            id="problem-footer",
        )

    def on_mount(self) -> None:
        self._populate_problems()
        self.query_one("#problem-preview-pane", Vertical).border_title = " preview "
        self.query_one("#problem-list-pane", Vertical).border_title = " cards "

    def on_screen_resume(self) -> None:
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

        if self._problems:
            lv.index = 0
            lv.focus()

        if not unsynced:
            self.query_one("#problem-status", Static).update(
                "  No unsolved problems. Run 'cram sync' or create a new one."
            )

    def action_cursor_down(self) -> None:
        self.query_one("#problem-list", ListView).action_cursor_down()

    def action_cursor_up(self) -> None:
        self.query_one("#problem-list", ListView).action_cursor_up()

    def on_list_view_selected(self, event: ListView.Selected) -> None:
        idx = event.index
        if idx == 0:
            self.app.push_screen(CreateProblem())
            return

        if idx - 1 >= len(getattr(self, "_problems", [])):
            return
        card = self._problems[idx - 1]
        self._rating_card_id = card.get("id")
        self.app.call_later(self._do_open_editor, card)

    def _do_open_editor(self, card: dict) -> None:
        import os
        import time

        from srs.templates import problem_template, sanitize_filename

        vault = config.vault()
        folder = config.problem_folder()
        notes_dir = vault / folder
        notes_dir.mkdir(parents=True, exist_ok=True)

        filename = sanitize_filename(card.get("title", "untitled")) + ".md"
        filepath = notes_dir / filename

        if not filepath.exists():
            try:
                filepath.write_text(
                    problem_template(
                        card.get("title", "Untitled"),
                        card.get("link", ""),
                        card.get("topic", ""),
                    ),
                    encoding="utf-8",
                )
            except OSError as e:
                self.notify(f"Failed to create file: {e}", severity="error")
                return

        card["folder"] = folder
        card["filename"] = filename
        data = cards.load_cards(config.cards_file())
        for c in data.get("problem_cards", []):
            if c.get("id") == card.get("id"):
                c["folder"] = folder
                c["filename"] = filename
                break
        cards.save_cards(config.cards_file(), data)

        try:
            text = filepath.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError) as e:
            text = f"(error reading file: {e})"
        preview = text[:800] + ("..." if len(text) > 800 else "")
        self.query_one("#problem-preview-content", Markdown).update(preview)
        self.query_one(
            "#problem-preview-pane", Vertical
        ).border_title = f" preview: {filepath.name} "
        self.query_one("#problem-status", Static).update(f"  Opening editor: {filepath.name}")

        editor = find_editor()
        if not editor:
            self.notify("No editor found. Set $EDITOR or install nvim/vi.", severity="error")
            self.query_one("#problem-status", Static).update("  Rate your recall (no editor):")
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

        time.sleep(0.1)
        self.app.refresh()

        try:
            text = filepath.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError) as e:
            text = f"(error reading file: {e})"
        preview = text[:800] + ("..." if len(text) > 800 else "")
        self.query_one("#problem-preview-content", Markdown).update(preview)
        self.query_one("#problem-status", Static).update("  Rate your recall:")
        from srs.screens.rating_dialog import RatingDialog

        self.app.push_screen(
            RatingDialog(card, config.desired_retention()),
            self._on_rate_result,
        )

    def action_go_back(self) -> None:
        self.app.pop_screen()

    def _on_rate_result(self, grade: int | None) -> None:
        if grade is None:
            self.query_one("#problem-status", Static).update("  Rating cancelled.")
            self.query_one("#problem-list", ListView).focus()
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

        self.app.pop_screen()
