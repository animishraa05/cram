# cram

Spaced repetition TUI for problems and concepts with FSRS-4.5 scheduling.

## Features

- **LeetCode Sync** — auto-imports your last-24h accepted submissions
- **Add Problems** — pick from synced LeetCode problems, write notes in nvim, rate recall
- **Add Concepts** — organize notes by subject (networking, DBMS, OS, etc.)
- **Review Due** — revisit cards when the forgetting curve says you should
- **FSRS-4.5** — state-of-the-art scheduling algorithm (20-30% fewer reviews than SM-2)
- **Desktop Notifications** — dunst notifications for due reviews
- **Theme System** — 8 built-in themes (tokyonight, dracula, gruvbox, nord, catppuccin, solarized, forest, default)
- **First-Run Wizard** — guides new users through initial setup

## Install

```bash
git clone https://github.com/animishraa05/cram.git
cd cram
make install
```

Or without make:

```bash
pip install .
```

For development:

```bash
make dev
```

## Usage

```bash
cram                  # Open TUI home screen
cram add-problem      # Directly open problem picker
cram add-concept      # Directly open concept form
cram review           # Directly open review queue
cram sync             # CLI-only: fetch last-24h LeetCode submissions
cram notify           # Send dunst notification for due cards
```

### Keybindings

| Key | Action |
|-----|--------|
| `q` | Quit |
| `1` | Add Problem |
| `2` | Add Concept |
| `3` | Review |
| `,` | Settings (theme selector) |

## Config

On first launch, the setup wizard will guide you through configuration. Config is stored at `~/.config/cram/config`:

```ini
CARDS_FILE="$HOME/cram/data/cards.json"
LEETCODE_USERNAME="your-leetcode-username"
OBSIDIAN_VAULT="$HOME/obsidian-vault"
PROBLEM_FOLDER="Private/Daily/Problems"
DESIRED_RETENTION=0.9
THEME="tokyonight"
```

### Themes

Available themes: `default`, `dracula`, `gruvbox`, `nord`, `tokyonight`, `catppuccin`, `solarized`, `forest`

Change theme via the settings screen (press `,`) or edit config directly.

## FSRS Algorithm

This project uses [FSRS-4.5](https://github.com/open-spaced-repetition/awesome-fsrs) with default parameters trained on 700M+ reviews from Anki users. It models:

- **Difficulty** (D) — per-card difficulty (1-10)
- **Stability** (S) — days until recall drops to 90%
- **Retrievability** (R) — current probability of recall

Rating buttons map to FSRS grades:

| Button | Grade | Meaning |
|--------|-------|---------|
| Again | 1 | Complete blackout |
| Hard | 2 | Significant effort to recall |
| Good | 3 | Some thought needed |
| Easy | 4 | Instant recall |

## Project Structure

```
cram/
├── srs/
│   ├── __init__.py       # Package init
│   ├── __main__.py       # python -m srs support
│   ├── app.py            # Main TUI app + CLI
│   ├── cards.py          # FSRS-4.5 algorithm + card CRUD
│   ├── config.py         # Config loader
│   ├── leetcode.py       # LeetCode GraphQL API
│   ├── notify.py         # dunst notifications
│   ├── templates.py      # Markdown note templates
│   ├── theme.py          # Theme system (8 presets)
│   ├── cram.tcss         # Textual CSS styles
│   └── screens/
│       ├── __init__.py
│       ├── home.py       # Main menu
│       ├── add_problem.py    # Add problem + create new
│       ├── add_concept.py    # Add concept
│       ├── review.py         # Review due cards
│       ├── rating.py         # Rating widget
│       ├── setup.py          # First-run wizard
│       └── settings.py       # Theme selector
├── tests/
│   ├── test_cards.py
│   ├── test_config.py
│   ├── test_templates.py
│   └── test_theme.py
├── data/
│   └── cards.json        # SRS card data (gitignored)
├── Makefile
├── pyproject.toml
├── LICENSE
└── README.md
```

## Testing

```bash
make test
```

Or:

```bash
pip install -e ".[dev]"
pytest tests/ -v
```

## License

MIT
