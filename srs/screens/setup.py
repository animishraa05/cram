"""First-run setup wizard — guides new users through initial configuration."""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical
from textual.screen import Screen
from textual.widgets import Button, Header, Input, Label, ListItem, ListView, Static

from srs.theme import THEMES

_EDITOR_CHOICES = [
    ("nvim", "Neovim (nvim)"),
    ("vim", "Vim (vim)"),
    ("vi", "Vi (vi)"),
    ("nano", "Nano (nano)"),
    ("hx", "Helix (hx)"),
    ("emacs", "Emacs (emacs)"),
    ("micro", "Micro (micro)"),
    ("obsidian", "Obsidian (obsidian)"),
    ("other", "Other — type a command below"),
]

# Steps (0-indexed):
#  0  Vault path
#  1  Problem folder
#  2  LeetCode username
#  3  Editor picker
#  4  Editor mode
#  5  Theme
#  6  Notifications
#  7  Cards file location
#  8  Git backup check
#  9  Anki import
# 10  Summary / confirm
# 11  Onboarding tips

_TOTAL = 12


_STEP_NAMES = [
    "Obsidian Vault", "Problem Folder", "LeetCode Username",
    "Editor", "Editor Mode", "Theme",
    "Notifications", "Cards Location", "Git Backup",
    "Import Cards", "Review & Confirm", "Quick Start Tips",
]


class SetupScreen(Screen):
    """Full first-run setup wizard."""

    BINDINGS = [
        ("escape", "quit_setup", "Quit"),
    ]

    CSS = """
    #setup-container {
        width: 78;
        max-width: 95%;
        padding: 2 3;
        background: $surface;
        overflow-y: auto;
    }
    #setup-welcome {
        text-style: bold;
        margin-bottom: 1;
        color: $primary;
    }
    #setup-step {
        color: $text-muted;
        margin-bottom: 1;
    }
    #setup-container Label {
        text-style: bold;
        margin-top: 1;
    }
    #setup-container Input {
        margin-bottom: 1;
    }
    #setup-status {
        color: $text-muted;
        margin-top: 1;
    }
    #setup-footer {
        color: $text-muted;
        margin-top: 1;
    }
    #theme-list, #editor-name-list {
        height: 12;
        border: solid $border;
        margin-bottom: 1;
        overflow-y: auto;
    }
    #editor-custom-input {
        margin-top: 0;
        margin-bottom: 1;
    }
    #editor-mode-list, #notify-list, #git-warn-list {
        height: 4;
        border: solid $border;
        margin-bottom: 1;
    }
    #cards-loc-list {
        height: 5;
        border: solid $border;
        margin-bottom: 1;
        overflow-y: auto;
    }
    #anki-file-input {
        margin-bottom: 1;
    }
    #summary-box {
        border: solid $border;
        padding: 1 2;
        margin-bottom: 1;
        color: $text;
    }
    #tips-box {
        border: solid $success;
        padding: 1 2;
        margin-bottom: 1;
        color: $text;
    }
    #confirm-btns {
        height: 3;
        margin-top: 1;
    }
    #confirm-btns Button {
        margin-right: 2;
    }
    """

    def compose(self) -> ComposeResult:
        yield Header()
        with Vertical(id="setup-container"):
            yield Static("  Welcome to cram  ", id="setup-welcome")
            yield Static(f"Step 1 of {_TOTAL}: Obsidian Vault", id="setup-step")

            # 0 — Vault
            yield Label("Path to your Obsidian vault (optional, leave blank for default):")
            yield Input(placeholder="~/vault  or  /home/user/notes", id="vault-input")

            # 1 — Folder
            yield Label(
                "Problem folder inside vault (Enter for default):", id="folder-label"
            )
            yield Input(placeholder="Private/Daily/Problems", id="folder-input")

            # 2 — LeetCode
            yield Label(
                "LeetCode username (optional — Enter to skip):", id="leetcode-label"
            )
            yield Input(placeholder="yourLChandle", id="leetcode-input")

            # 3 — Editor picker
            yield Label(
                "Which editor do you use? (j/k, Enter to confirm):",
                id="editor-name-label",
            )
            yield ListView(id="editor-name-list")
            yield Input(
                placeholder="custom command (e.g. code, kak) — leave blank to use list",
                id="editor-custom-input",
            )

            # 4 — Editor mode
            yield Label(
                "How should cram open notes? (j/k, Enter):", id="editor-mode-label"
            )
            yield ListView(id="editor-mode-list")

            # 5 — Theme
            yield Label(
                "Choose a colour theme (j/k = browse live, Enter = confirm):",
                id="theme-label",
            )
            yield ListView(id="theme-list")

            # 6 — Notifications
            yield Label(
                "Enable dunst desktop notifications for due cards?",
                id="notify-label",
            )
            yield ListView(id="notify-list")

            # 7 — Cards file location
            yield Label(
                "Where should cards.json be stored? (j/k, Enter):",
                id="cards-loc-label",
            )
            yield ListView(id="cards-loc-list")
            yield Input(
                placeholder="custom path (leave blank to use selection above)",
                id="cards-loc-input",
            )

            # 8 — Git backup check
            yield Static("", id="git-warn-box")
            yield Label(
                "Git auto-backup status for your vault:", id="git-warn-label"
            )
            yield ListView(id="git-warn-list")

            # 9 — Anki import
            yield Label(
                "Import cards from an Anki TSV export? (optional):",
                id="anki-label",
            )
            yield Input(
                placeholder="path to anki_export.txt — leave blank to skip",
                id="anki-file-input",
            )

            # 10 — Summary / confirm
            yield Static("", id="summary-box")
            with Horizontal(id="confirm-btns"):
                yield Button("  Confirm & Save  ", id="confirm-btn", variant="success")
                yield Button("  ← Go back  ", id="back-btn", variant="default")

            # 11 — Tips
            yield Static("", id="tips-box")

            yield Static("", id="setup-status")
            yield Static("← Back   Esc: quit", id="setup-footer")

    # ── mount ──────────────────────────────────────────────────────────

    def on_mount(self) -> None:
        self._step = 0
        self._cfg: dict[str, str] = {}
        self._pending_vault: Path | None = None
        self._anki_imported = 0

        # Detect available editors
        self._available: set[str] = {
            cmd for cmd, _ in _EDITOR_CHOICES
            if cmd != "other" and shutil.which(cmd)
        }

        # Build editor-name list
        en = self.query_one("#editor-name-list", ListView)
        for cmd, label in _EDITOR_CHOICES:
            mark = " ✓" if cmd in self._available else ""
            en.append(ListItem(Label(f"{label}{mark}"), id=f"en-{cmd}"))
        for i, (cmd, _) in enumerate(_EDITOR_CHOICES):
            if cmd in self._available:
                en.index = i
                break

        # Editor mode list
        em = self.query_one("#editor-mode-list", ListView)
        em.append(ListItem(
            Label("external  — open in your terminal editor (suspends TUI)"),
            id="em-external",
        ))
        em.append(ListItem(
            Label("embedded  — inline editor inside the cram TUI window"),
            id="em-embedded",
        ))
        em.index = 1

        # Theme list
        tl = self.query_one("#theme-list", ListView)
        for name in THEMES:
            tl.append(ListItem(Label(name), id=f"theme-{name}"))
        names = list(THEMES.keys())
        if "tokyonight" in names:
            tl.index = names.index("tokyonight")

        # Notifications list
        nl = self.query_one("#notify-list", ListView)
        dunst_ok = bool(shutil.which("dunstify") or shutil.which("dunst"))
        dunst_note = " (dunst detected ✓)" if dunst_ok else " (dunst NOT found — install dunst)"
        nl.append(ListItem(Label(f"Yes — enable hourly reminders{dunst_note}"), id="notify-yes"))
        nl.append(ListItem(Label("No  — I'll check cram manually"), id="notify-no"))
        nl.index = 0 if dunst_ok else 1

        # Cards location list (populated later when vault is known)
        cl = self.query_one("#cards-loc-list", ListView)
        cl.append(ListItem(Label("Default: ~/.local/share/cram/cards.json"), id="cl-default"))
        cl.append(ListItem(Label("Inside vault (good for git backup)"), id="cl-vault"))
        cl.append(ListItem(Label("Custom path — type below"), id="cl-custom"))
        cl.index = 0

        # Git warn list (acknowledge)
        gw = self.query_one("#git-warn-list", ListView)
        gw.append(ListItem(Label("OK — I'll set up git remote later"), id="gw-later"))
        gw.append(ListItem(Label("Skip git backup entirely (not recommended)"), id="gw-skip"))
        gw.index = 0

        self._show_only_step(0)
        self.query_one("#cards-loc-input", Input).display = False
        self.query_one("#vault-input", Input).focus()

    # ── step widget map ────────────────────────────────────────────────

    _STEP_WIDGETS: dict[int, list[str]] = {
        0:  ["vault-input"],
        1:  ["folder-label", "folder-input"],
        2:  ["leetcode-label", "leetcode-input"],
        3:  ["editor-name-label", "editor-name-list", "editor-custom-input"],
        4:  ["editor-mode-label", "editor-mode-list"],
        5:  ["theme-label", "theme-list"],
        6:  ["notify-label", "notify-list"],
        7:  ["cards-loc-label", "cards-loc-list"],
        8:  ["git-warn-box", "git-warn-label", "git-warn-list"],
        9:  ["anki-label", "anki-file-input"],
        10: ["summary-box", "confirm-btns"],
        11: ["tips-box"],
    }

    _STEP_NAMES = [
        "Obsidian Vault", "Problem Folder", "LeetCode Username",
        "Editor", "Editor Mode", "Theme",
        "Notifications", "Cards Location", "Git Backup",
        "Import Cards", "Review & Confirm", "Quick Start Tips",
    ]

    def _step_label(self, step: int) -> str:
        name = self._STEP_NAMES[step] if 0 <= step < len(self._STEP_NAMES) else ""
        return f"Step {step + 1} of {_TOTAL}: {name}"

    def _show_only_step(self, step: int) -> None:
        all_ids = [w for ids in self._STEP_WIDGETS.values() for w in ids]
        visible = set(self._STEP_WIDGETS.get(step, []))
        for wid_id in all_ids:
            try:
                self.query_one(f"#{wid_id}").display = wid_id in visible
            except Exception:
                pass

    def _focus_step(self, step: int) -> None:
        focus_map = {
            0: "#vault-input", 1: "#folder-input", 2: "#leetcode-input",
            3: "#editor-name-list", 4: "#editor-mode-list", 5: "#theme-list",
            6: "#notify-list", 7: "#cards-loc-list", 8: "#git-warn-list",
            9: "#anki-file-input", 10: "#confirm-btn", 11: "#tips-box",
        }
        sel = focus_map.get(step)
        if sel:
            try:
                self.query_one(sel).focus()
            except Exception:
                pass

    def _advance(self, next_step: int, hint: str = "") -> None:
        self._step = next_step
        self.query_one("#setup-step", Static).update(self._step_label(next_step))
        if hint:
            self.query_one("#setup-status", Static).update(hint)
        if next_step != 7:
            try:
                self.query_one("#cards-loc-input", Input).display = False
            except Exception:
                pass
        self._show_only_step(next_step)
        self._focus_step(next_step)

    # ── navigation ─────────────────────────────────────────────────────

    def action_quit_setup(self) -> None:
        self.app.exit()

    def key_left(self) -> None:
        if self._step <= 0:
            return
        self._advance(self._step - 1)

    # ── input / button handlers ────────────────────────────────────────

    def on_input_submitted(self, event: Input.Submitted) -> None:
        handlers = {
            "vault-input": self._handle_vault,
            "folder-input": self._handle_folder,
            "leetcode-input": self._handle_leetcode,
            "editor-custom-input": self._handle_editor_name,
            "cards-loc-input": self._handle_cards_loc,
            "anki-file-input": self._handle_anki,
        }
        fn = handlers.get(event.input.id or "")
        if fn:
            fn()

    def key_enter(self) -> None:
        step_handlers = {
            3: self._handle_editor_name,
            4: self._handle_editor_mode,
            5: self._handle_theme,
            6: self._handle_notifications,
            7: self._handle_cards_loc,
            8: self._handle_git_warn,
            11: self._exit_setup,
        }
        fn = step_handlers.get(self._step)
        if fn:
            fn()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "confirm-btn":
            self._finish_setup()
        elif event.button.id == "back-btn":
            self.key_left()

    def on_list_view_highlighted(self, event: ListView.Highlighted) -> None:
        if event.list_view.id == "theme-list" and self._step == 5:
            names = list(THEMES.keys())
            idx = event.list_view.index
            if idx is not None and 0 <= idx < len(names):
                self.app.theme = f"cram-{names[idx]}"
        elif event.list_view.id == "cards-loc-list" and self._step == 7:
            idx = event.list_view.index or 0
            inp = self.query_one("#cards-loc-input", Input)
            if idx == 2:
                inp.display = True
                inp.focus()
            else:
                inp.display = False

    # ── step handlers ──────────────────────────────────────────────────

    def _handle_vault(self) -> None:
        if self._pending_vault is not None:
            self._pending_vault = None
            raw = self.query_one("#vault-input", Input).value.strip()
            self._apply_vault(Path(raw).expanduser().resolve() if raw else None)
            return

        raw = self.query_one("#vault-input", Input).value.strip()
        if not raw:
            self._apply_vault(None)
            return

        vault = Path(raw).expanduser().resolve()
        if not vault.exists():
            self._pending_vault = vault
            self.query_one("#setup-status", Static).update(
                f"  '{vault}' doesn't exist — create it? (Enter to confirm)"
            )
            return
        self._apply_vault(vault)

    def _apply_vault(self, vault: Path | None) -> None:
        if vault is not None:
            vault.mkdir(parents=True, exist_ok=True)
            self._cfg["OBSIDIAN_VAULT"] = str(vault)
            vault_path_str = str(vault)
        else:
            self._cfg["OBSIDIAN_VAULT"] = ""
            vault_path_str = "Default local notes"
        # Update cards-loc list to include vault-relative option
        try:
            cl = self.query_one("#cards-loc-list", ListView)
            cl.clear()
            default_path = (
                Path.home() / ".local" / "share" / "cram" / "cards.json"
            )
            cl.append(ListItem(
                Label(f"Default: {default_path}"), id="cl-default"
            ))
            if vault is not None:
                vault_path = vault / ".cram" / "cards.json"
                cl.append(ListItem(
                    Label(f"In vault: {vault_path}  (synced via git ✓)"), id="cl-vault"
                ))
            cl.append(ListItem(Label("Custom path — type below"), id="cl-custom"))
            cl.index = 0
        except Exception:
            pass
        self._advance(1, hint=f"  Vault: {vault_path_str}")

    def _handle_folder(self) -> None:
        folder = self.query_one("#folder-input", Input).value.strip()
        self._cfg["PROBLEM_FOLDER"] = folder or "Private/Daily/Problems"
        self._advance(2)

    def _handle_leetcode(self) -> None:
        username = self.query_one("#leetcode-input", Input).value.strip()
        if username:
            self._cfg["LEETCODE_USERNAME"] = username
        self._advance(3, hint="  ✓ installed editors marked. Pick one or type below.")

    def _handle_editor_name(self) -> None:
        custom = self.query_one("#editor-custom-input", Input).value.strip()
        if custom:
            self._cfg["EDITOR"] = custom
            self._advance(4, hint=f"  Editor: {custom}")
            return

        en = self.query_one("#editor-name-list", ListView)
        idx = en.index
        if idx is None:
            self.query_one("#setup-status", Static).update(
                "  Pick an editor from the list or type a command below."
            )
            return

        cmd = _EDITOR_CHOICES[idx][0]
        if cmd == "other":
            self.query_one("#editor-custom-input", Input).focus()
            self.query_one("#setup-status", Static).update(
                "  Type your editor command and press Enter."
            )
            return

        if cmd not in self._available:
            self.query_one("#setup-status", Static).update(
                f"  '{cmd}' not found in PATH. Type a custom command below or pick another."
            )
            return

        self._cfg["EDITOR"] = cmd
        self._advance(4, hint=f"  Editor: {cmd}")

    def _handle_editor_mode(self) -> None:
        em = self.query_one("#editor-mode-list", ListView)
        mode = "external" if (em.index or 0) == 0 else "embedded"
        self._cfg["EDITOR_MODE"] = mode
        self._advance(5, hint="  j/k to browse themes — they apply live!")

    def _handle_theme(self) -> None:
        tl = self.query_one("#theme-list", ListView)
        idx = tl.index
        names = list(THEMES.keys())
        theme = names[idx] if idx is not None and 0 <= idx < len(names) else "tokyonight"
        self._cfg["THEME"] = theme
        self._advance(6)

    def _handle_notifications(self) -> None:
        nl = self.query_one("#notify-list", ListView)
        enabled = (nl.index or 0) == 0
        self._cfg["NOTIFY_ENABLED"] = "true" if enabled else "false"
        self._cfg["NOTIFY_INTERVAL"] = "3600"
        hint = "  Notifications enabled — install dunst if not already." if enabled else ""
        self._advance(7, hint=hint)

    def _handle_cards_loc(self) -> None:
        custom_path = self.query_one("#cards-loc-input", Input).value.strip()
        cl = self.query_one("#cards-loc-list", ListView)
        idx = cl.index or 0

        if custom_path:
            self._cfg["CARDS_FILE"] = custom_path
        elif idx == 1:
            vault_str = self._cfg.get("OBSIDIAN_VAULT", "")
            if vault_str:
                vault = Path(vault_str)
                self._cfg["CARDS_FILE"] = str(vault / ".cram" / "cards.json")
            else:
                # Vault not configured — fall through to default
                pass
        elif idx == 2:
            self.query_one("#cards-loc-input", Input).focus()
            self.query_one("#setup-status", Static).update(
                "  Enter a custom path and press Enter."
            )
            return
        # else: idx==0, leave CARDS_FILE empty → use default

        self._check_git_and_advance()

    def _check_git_and_advance(self) -> None:
        """Check vault git status and show warning if no remote."""
        vault_str = self._cfg.get("OBSIDIAN_VAULT", "")
        if not vault_str:
            # No Obsidian vault configured — git backup doesn't apply, skip to anki
            self._advance(9, hint="  No vault set — git backup skipped.")
            return

        vault = Path(vault_str)
        has_git = False
        has_remote = False

        if vault.exists():
            try:
                r = subprocess.run(
                    ["git", "rev-parse", "--is-inside-work-tree"],
                    cwd=vault, capture_output=True, timeout=5, check=False,
                )
                has_git = r.returncode == 0
                if has_git:
                    r2 = subprocess.run(
                        ["git", "remote"],
                        cwd=vault, capture_output=True, text=True, timeout=5, check=False,
                    )
                    has_remote = bool(r2.stdout.strip())
            except Exception:
                pass

        box = self.query_one("#git-warn-box", Static)
        if not has_git:
            box.update(
                "  ⚠  Your vault is NOT a git repo.\n"
                "  cram's auto-backup won't work until you run:\n"
                "    git init && git remote add origin <your-remote-url>\n"
                "  inside your vault."
            )
        elif not has_remote:
            box.update(
                "  ⚠  Vault is a git repo but has NO remote.\n"
                "  Auto-backup commits locally but can't push.\n"
                "  Add a remote with:  git remote add origin <url>"
            )
        else:
            box.update("  ✓  Vault git repo with remote detected — auto-backup is ready!")
            # No warning needed, skip straight to anki
            self._advance(9, hint="  Vault git is configured. Auto-backup will work.")
            return

        self._advance(8)

    def _handle_git_warn(self) -> None:
        self._advance(9)

    def _handle_anki(self) -> None:
        path = self.query_one("#anki-file-input", Input).value.strip()
        if path:
            try:
                from srs.cards import find_card_by_title, load_cards, make_card, save_cards

                # Use the cards path from self._cfg (not yet saved to disk)
                from srs.config import cards_file as _default_cards_file

                cards_path = (
                    Path(self._cfg["CARDS_FILE"])
                    if "CARDS_FILE" in self._cfg
                    else _default_cards_file()
                )
                cards_path.parent.mkdir(parents=True, exist_ok=True)
                data = load_cards(cards_path)
                count = 0
                with open(path, encoding="utf-8") as fh:
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
                        if not find_card_by_title(data, title, "problem"):
                            card = make_card("problem", title, topic=topic)
                            data.setdefault("problem_cards", []).append(card)
                            count += 1
                if count > 0:
                    save_cards(cards_path, data)
                self._anki_imported = count
                hint = f"  Imported {count} new cards from Anki export."
            except Exception as e:
                hint = f"  Import failed: {e}"
            self.query_one("#setup-status", Static).update(hint)
        self._build_summary()
        self._advance(10)

    def _build_summary(self) -> None:
        vault = self._cfg.get("OBSIDIAN_VAULT", "") or "(local default: ~/.local/share/cram/notes)"
        folder = self._cfg.get("PROBLEM_FOLDER", "Private/Daily/Problems")
        lc = self._cfg.get("LEETCODE_USERNAME", "") or "—"
        editor = self._cfg.get("EDITOR", "auto-detect") or "auto-detect"
        mode = self._cfg.get("EDITOR_MODE", "embedded")
        theme = self._cfg.get("THEME", "tokyonight")
        notify = self._cfg.get("NOTIFY_ENABLED", "false")
        cards_loc = self._cfg.get("CARDS_FILE", "") or "~/.local/share/cram/cards.json"
        anki = f"{self._anki_imported} cards imported" if self._anki_imported else "skipped"

        summary = (
            f"  Vault          {vault}\n"
            f"  Problem folder {folder}\n"
            f"  LeetCode user  {lc}\n"
            f"  Editor         {editor}  [{mode} mode]\n"
            f"  Theme          {theme}\n"
            f"  Notifications  {notify}\n"
            f"  Cards file     {cards_loc}\n"
            f"  Anki import    {anki}\n\n"
            "  Press [Confirm & Save] to finish, or ← to go back."
        )
        self.query_one("#summary-box", Static).update(summary)

    def _finish_setup(self) -> None:
        from srs.config import cards_file, save_config

        if "CARDS_FILE" not in self._cfg:
            self._cfg["CARDS_FILE"] = str(cards_file())

        save_config(self._cfg)
        self.app.theme = f"cram-{self._cfg.get('THEME', 'tokyonight')}"

        cards_path = Path(self._cfg["CARDS_FILE"])
        cards_path.parent.mkdir(parents=True, exist_ok=True)
        if not cards_path.exists():
            cards_path.write_text(
                '{"problem_cards": [], "concept_cards": []}', encoding="utf-8"
            )

        # Wire up systemd notifications if user enabled them
        try:
            from srs.notifications import remove_notifications, setup_notifications
            if self._cfg.get("NOTIFY_ENABLED", "false").lower() in ("true", "1", "yes"):
                setup_notifications()  # creates systemd user timer
            else:
                remove_notifications() # removes systemd user timer
        except Exception:
            pass  # non-fatal — in-app notifications still work

        self._build_tips()
        self._advance(11, hint="  Config saved. Read the tips below, then press Enter.")

    def _build_tips(self) -> None:
        tips = (
            "  Quick-start cheat sheet\n"
            "  ───────────────────────────────────────────────────────\n"
            "  Navigation          j / k  or  ↑ / ↓  — move cursor\n"
            "                      Enter  — open / confirm\n"
            "                      Esc    — go back\n"
            "                      q      — quit (with confirm)\n\n"
            "  Home screen         r  — start review session\n"
            "                      a  — add problem\n"
            "                      c  — add concept\n"
            "                      b  — browse all cards\n"
            "                      s  — settings & theme\n\n"
            "  Review              1 Again  2 Hard  3 Good  4 Easy\n\n"
            "  CLI shortcuts\n"
            "    cram sync          fetch today's LeetCode ACs\n"
            "    cram review        open review queue directly\n"
            "    cram export        export cards as CSV\n"
            "    cram notify        send a dunst notification\n\n"
            "  Config file         ~/.config/cram/config\n"
            f"  Cards file          "
            f"{self._cfg.get('CARDS_FILE', '~/.local/share/cram/cards.json')}\n\n"
            "  Press Enter to launch cram →"
        )
        self.query_one("#tips-box", Static).update(tips)

    def _exit_setup(self) -> None:
        self.app.switch_screen("home")
