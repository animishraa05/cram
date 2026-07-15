# Contributing to cram

## Development Setup

```bash
git clone https://github.com/animishraa05/cram.git
cd cram
make dev        # Installs in editable mode with dev dependencies
make test       # Runs pytest suite
make lint       # Checks code quality (ruff check + mypy)
make format     # Auto-formats code (ruff format)
```

---

## Project Structure

- `srs/` — main package
  - `app.py` — CLI entry point + CramApp setup
  - `cards.py` — FSRS-4.5 scheduling engine
  - `config.py` — Configuration file manager
  - `editor.py` — CLI editor detector
  - `git_sync.py` — Git Auto-Sync background runner
  - `leetcode.py` — LeetCode GraphQL API client
  - `obsidian.py` — Obsidian vault scanner
  - `export.py` — CSV export + Anki TSV import
  - `notify.py` — Desktop notification client
  - `templates.py` — Markdown templates
  - `theme.py` — Color theme configuration presets
  - `cram.tcss` — Textual CSS styling
  - `screens/` — Textual Screen controllers:
    - `home.py` — Command dashboard
    - `add_problem.py` — Problem loader screen
    - `add_concept.py` — Concept form screen
    - `browse.py` — Search/edit/delete card browser
    - `editor.py` — TextArea inline markdown editor
    - `review.py` — Review queue screen
    - `rating_dialog.py` — FSRS horizontal rating modal
    - `confirm.py` — Dialog modal (quit/delete)
    - `settings.py` — Theme chooser + config inputs
    - `setup.py` — First-run configuration wizard
- `tests/` — pytest test suite
- `data/` — card data directory (gitignored)

---

## Code Style Guidelines

- Python 3.10+ with type hints.
- Ruff for linting and code formatting.
- MyPy for strict type checking.
- Document and preserve existing comments.
- Follow the custom dual-pane TUI aesthetic and Vim keybindings.

---

## Testing

```bash
make test
```

Tests use pytest. Mock external APIs (LeetCode, systemd, dunstify) with `unittest.mock`.

---

## Pull Requests

1. Fork and create a feature branch from `main`.
2. Make changes with tests where applicable.
3. Run `make lint` and `make test`.
4. Open a PR with a clear, concise description.
