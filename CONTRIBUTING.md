# Contributing to cram

## Development Setup

```bash
git clone https://github.com/animishraa05/cram.git
cd cram
make dev        # installs in editable mode with dev deps
make test       # run tests
make lint       # check code quality
make format     # auto-format code
```

## Project Structure

- `srs/` — main package
  - `app.py` — CLI entry + TUI app
  - `cards.py` — FSRS-4.5 algorithm + card CRUD
  - `config.py` — config loader
  - `leetcode.py` — LeetCode GraphQL API
  - `obsidian.py` — Obsidian vault scanner
  - `export.py` — CSV export + Anki import
  - `editor.py` — editor detection
  - `notify.py` — desktop notifications
  - `templates.py` — markdown templates
  - `theme.py` — color themes
  - `screens/` — TUI screens
- `tests/` — pytest test suite
- `data/` — card data (gitignored)

## Code Style

- Python 3.10+ with type hints
- Ruff for linting and formatting
- MyPy for type checking
- No comments unless asked
- Follow existing patterns

## Testing

```bash
make test
```

Tests use pytest. Mock external APIs (LeetCode, dunstify) with `unittest.mock`.

## Pull Requests

1. Fork and create a feature branch
2. Make changes with tests
3. Run `make lint` and `make test`
4. Open a PR with a clear description
