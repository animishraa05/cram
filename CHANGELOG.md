# Changelog

All notable changes to cram, organized by phase. Each entry includes the file(s) changed and what to revert if needed.

---

## Phase 1: Critical Bugs

### FIX #1 — Review loop (`review.py`)
**File:** `srs/screens/review.py`
**What:** After rating a card, refresh the due list instead of popping to home. Only pop when no cards remain.
**Revert:** Restore `on_rating_rated` to call `self.app.pop_screen()` unconditionally.

### FIX #2 — New card detection (`cards.py`)
**File:** `srs/cards.py`
**What:** Added `review_count` field to `make_card()`. Changed new-card check in `update_card` from `repetition==0 and interval==1` to `review_count == 0`. Increment `review_count` after each review.
**Revert:** Remove `review_count` from `make_card`, restore old condition in `update_card`.

### FIX #3 — Key binding conflicts (`app.py`, `rating.py`)
**Files:** `srs/app.py`, `srs/screens/rating.py`, `srs/screens/home.py`, `srs/cram.tcss`
**What:** Removed global `key_1/2/3` from CramApp. Added `BINDINGS` to HomeScreen. Changed rating keys from `1/2/3/4` to `a/h/g/e`. Updated rating button labels.
**Revert:** Restore global key_1/2/3 in app.py, restore 1/2/3/4 keys in rating.py.

### FIX #4 — next() without default (`leetcode.py`)
**File:** `srs/leetcode.py`
**What:** Built `sub_map` dict before loop in `sync_leetcode` instead of using `next()` generator.
**Revert:** Restore `next(s for s in recent if s["titleSlug"] == slug)`.

### FIX #5 — Grade validation (`cards.py`)
**File:** `srs/cards.py`
**What:** Added `if not 1 <= grade <= 4: raise ValueError(...)` at top of `update_card`, `initial_stability`, `initial_difficulty`.
**Revert:** Remove validation guards.

### FIX #6 — Remove dead `ease_factor` (`cards.py`)
**File:** `srs/cards.py`
**What:** Removed `ease_factor` from `make_card()` and `update_card()`.
**Revert:** Add `"ease_factor": 2.5` back to `make_card`, restore computation in `update_card`.

---

## Phase 2: UX/UI Improvements

### UX #7 — Stale stats (`home.py`)
**File:** `srs/screens/home.py`
**What:** Added `on_screen_resume` to call `_update_stats()` when returning from other screens.
**Revert:** Remove `on_screen_resume` method.

### UX #8 — Sync shortcut (`home.py`)
**File:** `srs/screens/home.py`
**What:** Added `s` key binding for sync in HomeScreen. Updated footer text.
**Revert:** Remove `s` binding, restore old footer.

### UX #9 — Card preview in review (`review.py`)
**File:** `srs/screens/review.py`
**What:** Added preview pane showing title/topic/link when a card is selected.
**Revert:** Remove preview widgets and `on_list_view_selected` preview logic.

### UX #10 — Fix "tab: switch" lie (`settings.py`)
**File:** `srs/screens/settings.py`
**What:** Removed "tab: switch" from footer text.
**Revert:** Add text back.

### UX #11 — Editable config in settings (`settings.py`)
**File:** `srs/screens/settings.py`
**What:** Added editable Input widgets for DESIRED_RETENTION, LEETCODE_USERNAME, OBSIDIAN_VAULT, PROBLEM_FOLDER. Save on confirm.
**Revert:** Remove input widgets, restore read-only display.

### UX #12 — Vault creation confirmation (`setup.py`)
**File:** `srs/screens/setup.py`
**What:** Added confirmation step before creating vault directory.
**Revert:** Remove confirmation, restore direct mkdir.

### UX #13 — Back navigation in setup (`setup.py`)
**File:** `srs/screens/setup.py`
**What:** Added back key handling to return to previous wizard step.
**Revert:** Remove back navigation logic.

### UX #14 — Rating visual feedback (`rating.py`)
**File:** `srs/screens/rating.py`
**What:** Added brief delay before posting rating message to show button press feedback.
**Revert:** Remove timer, restore immediate post.

### UX #15 — Back to change subject (`add_concept.py`)
**File:** `srs/screens/add_concept.py`
**What:** Added back key during title step to return to subject step.
**Revert:** Remove back navigation.

### UX #16 — Fallback editor (`add_problem.py`, `add_concept.py`, `review.py`)
**Files:** `srs/screens/add_problem.py`, `srs/screens/add_concept.py`, `srs/screens/review.py`
**What:** Created `srs/editor.py` with `find_editor()` that tries $EDITOR > $VISUAL > nvim > vi. Updated all screens to use it.
**Revert:** Delete `srs/editor.py`, restore `shutil.which("nvim")` checks.

### UX #17 — Remove hardcoded black bg (`cram.tcss`)
**File:** `srs/cram.tcss`
**What:** Removed `Screen { background: #000000; }` rule.
**Revert:** Add rule back.

### UX #18 — Fix unused theme fields (`theme.py`, `app.py`)
**Files:** `srs/theme.py`, `srs/app.py`
**What:** Registered theme `muted`/`text`/`sub_text` colors as Textual CSS variables in CramApp.
**Revert:** Remove variable registrations.

---

## Phase 3: Backend/Logic

### BE #19 — review_count field
Combined with FIX #2 above.

### BE #20 — Grade validation
Combined with FIX #5 above.

### BE #21 — Backup corrupted cards.json (`cards.py`)
**File:** `srs/cards.py`
**What:** In `load_cards`, rename corrupted file to `.json.corrupt` before returning fresh dict.
**Revert:** Remove backup logic.

### BE #22 — Cap reviews array (`cards.py`)
**File:** `srs/cards.py`
**What:** Truncate `reviews` to last 100 entries in `update_card`.
**Revert:** Remove truncation line.

### BE #23 — Validate DESIRED_RETENTION (`config.py`)
**File:** `srs/config.py`
**What:** Clamp `desired_retention()` return to 0.0-1.0 range.
**Revert:** Remove clamp.

### BE #24 — XDG compliance (`config.py`)
**File:** `srs/config.py`
**What:** Changed default cards path to `~/.local/share/cram/cards.json`. Added migration from old path.
**Revert:** Restore old default path, remove migration.

### BE #25 — Check dunstify (`notify.py`)
**File:** `srs/notify.py`
**What:** Added `shutil.which("dunstify")` check. Print count on success.
**Revert:** Remove check, restore silent behavior.

### BE #26 — Escape YAML quotes (`templates.py`)
**File:** `srs/templates.py`
**What:** Escape `"` in title for YAML frontmatter.
**Revert:** Remove escaping.

### BE #27 — Truncate filenames (`templates.py`)
**File:** `srs/templates.py`
**What:** Truncate `sanitize_filename` result to 200 chars.
**Revert:** Remove truncation.

### BE #28 — Check GraphQL errors (`leetcode.py`)
**File:** `srs/leetcode.py`
**What:** Check for `"errors"` key in GraphQL response after `graphql_query`.
**Revert:** Remove error check.

### BE #29 — Add logging
**Files:** all modules with `print()`
**What:** Added `logging` module usage. Replaced `print()` warnings with `logger.warning()`. Added basic config in `app.py`.
**Revert:** Replace logger calls back with print.

---

## Phase 4: New Functionalities

### FEAT #30 — Browse/Search screen
**Files:** `srs/screens/browse.py` (new), `srs/app.py`, `srs/screens/home.py`
**What:** New screen listing all cards with filter (all/new/due/reviewed) and search by title/topic.
**Revert:** Delete `srs/screens/browse.py`, remove from SCREENS dict and home menu.

### FEAT #31 — Edit/Delete cards
**File:** `srs/screens/browse.py`
**What:** Added `d` key to delete (with confirmation), `e` to edit title/topic.
**Revert:** Remove key handlers from browse.py.

### FEAT #32 — Export/Import
**Files:** `srs/app.py`, `srs/export.py` (new)
**What:** Added `cram export --format csv` and `cram import --from anki` CLI subcommands.
**Revert:** Delete `srs/export.py`, remove subcommands from app.py.

### FEAT #33 — Stats/Dashboard
**Files:** `srs/cards.py`, `srs/screens/home.py`
**What:** Added `compute_stats()` to cards.py. Expanded home screen to show streak, retention rate, cards by topic.
**Revert:** Remove `compute_stats`, restore simple count display.

### FEAT #34 — Redesigned rating keys
Combined with FIX #3 above.

### FEAT #35 — In-TUI note editor
**File:** `srs/screens/editor.py` (new)
**What:** TextArea-based editor as fallback when no external editor found.
**Revert:** Delete `srs/screens/editor.py`.

### FEAT #36 — Configurable editor
**Files:** `srs/config.py`, `srs/editor.py`
**What:** Added `EDITOR` config option. Resolution: config > $EDITOR > $VISUAL > nvim > vi > in-TUI.
**Revert:** Remove EDITOR config option.

### FEAT #37 — Concept review from Obsidian
**File:** `srs/obsidian.py` (new)
**What:** Scan vault for markdown files with frontmatter `type: concept`. Import as concept cards via `cram sync-concepts`.
**Revert:** Delete `srs/obsidian.py`, remove subcommand.

---

## Phase 5: Tests

### TEST #38 — leetcode.py tests
**File:** `tests/test_leetcode.py` (new)
**What:** Tests for `filter_last_24h`, `sync_leetcode` dedup, `LeetCodeAPIError`, with mocked network.
**Revert:** Delete file.

### TEST #39 — cards.py additional tests
**File:** `tests/test_cards.py`
**What:** Added grade=2 test, multi-step sequences, invalid grade, `review_count` tests.
**Revert:** Remove added test functions.

### TEST #40 — config.py additional tests
**File:** `tests/test_config.py`
**What:** Added tests for `cards_file()`, `vault()`, `desired_retention()`, `is_configured()`, retention bounds.
**Revert:** Remove added test functions.

### TEST #41 — templates.py edge cases
**File:** `tests/test_templates.py`
**What:** Added tests for empty title, special chars, unicode, truncation.
**Revert:** Remove added test functions.

### TEST #42 — notify.py tests
**File:** `tests/test_notify.py` (new)
**What:** Tests for `notify_due` with mocked subprocess and missing dunstify.
**Revert:** Delete file.

---

## Phase 6: Dev Experience

### DX #43 — Ruff + MyPy
**Files:** `pyproject.toml`, `Makefile`
**What:** Added ruff/mypy to dev deps. Added tool config sections. Added `make lint` and `make format`.
**Revert:** Remove tool sections, remove make targets.

### DX #44 — CONTRIBUTING.md
**File:** `CONTRIBUTING.md` (new)
**What:** Dev setup, code style, PR guidelines.
**Revert:** Delete file.

### DX #45 — Document runtime deps in README
**File:** `README.md`
**What:** Added nvim/dunst to prerequisites. Added troubleshooting section.
**Revert:** Remove additions.

### DX #46 — Sync version
**File:** `srs/__init__.py`
**What:** Replaced hardcoded version with `importlib.metadata.version("cram")`.
**Revert:** Restore hardcoded version.
