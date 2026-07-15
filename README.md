# cram

Spaced repetition TUI for programming problems and academic concepts, powered by FSRS-4.5.

## What it does

cram helps you remember LeetCode problems and study concepts using spaced repetition. It syncs your recent LeetCode submissions, creates notes in your Obsidian vault, and schedules reviews when the forgetting curve says you should revisit a card.

## Install

### Prerequisites

**Required:**
- Python >= 3.10
- [pipx](https://pipx.pypa.io/stable/)

```bash
# Arch Linux
pacman -S python-pipx

# macOS
brew install pipx

# Other
pip install pipx
```

**Optional:**
- `nvim` or `vi` — for editing notes (falls back to `$EDITOR` / `$VISUAL`)
- `dunst` + `dunstify` — for desktop notifications

### Install cram

```bash
git clone https://github.com/animishraa05/cram.git
cd cram
make install
```

Or without make:

```bash
pipx install .
```

### Uninstall

```bash
make uninstall
# or: pipx uninstall cram
```

## Quick Start

1. Run `cram` — the setup wizard guides you through configuration
2. Set your Obsidian vault path, problem folder, and LeetCode username
3. Press `s` on the home screen to sync your recent LeetCode submissions
4. Press `3` to review due cards

## Usage

```bash
cram                  # Open TUI home screen
cram add-problem      # Open problem picker
cram add-concept      # Open concept form
cram review           # Open review queue
cram browse           # Browse all cards
cram sync             # CLI: fetch last-24h LeetCode submissions
cram sync-concepts    # CLI: import concepts from Obsidian vault
cram export           # CLI: export cards as CSV to stdout
cram import FILE      # CLI: import cards from Anki TSV export
cram notify           # CLI: send dunst notification for due cards
cram setup-notifications  # Enable hourly desktop notifications
cram remove-notifications # Disable hourly notifications
```

## How It Works

### Adding Problems

**Option 1: Sync from LeetCode**
- Press `s` on the home screen (or run `cram sync`)
- Problems solved in the last 24 hours are imported with topic tags
- Cards appear in the review queue **the next day**

**Option 2: Create manually**
- Press `1` on the home screen
- Select "[+] Create new problem..." or pick from unsynced problems
- Enter title, link, and topic
- Your editor opens with a note template — fill in your approach and solution
- After closing the editor, **rate your recall** (see Rating below)

### Adding Concepts

- Press `2` on the home screen
- Enter a subject (e.g., "Networking", "DBMS", "OS")
- Enter a concept title
- Your editor opens with a concept template
- After closing the editor, rate your recall

### Reviewing Cards

- Press `3` on the home screen
- The left pane shows due cards (sorted by urgency)
- Select a card — the note appears in the right pane
- **Rate your recall** using the Again/Hard/Good/Easy buttons

**Skip a card:** Press `n` to skip without rating.

**No cards due?** Cards synced from LeetCode become due the next day. Cards created manually are due immediately.

### Rating

After reviewing a card (or creating one), four buttons appear:

| Key | Rating | When to use |
|-----|--------|-------------|
| `a` | Again | Complete blackout — couldn't recall at all |
| `h` | Hard | Significant effort to recall |
| `g` | Good | Some thought needed, but got it |
| `e` | Easy | Instant recall, no effort |

The FSRS-4.5 algorithm uses your ratings to schedule the next review. Higher ratings = longer intervals before the next review.

### Browsing Cards

- Press `b` on the home screen
- Search by title or topic in the search bar
- Filter: `[a]` All, `[n]` New, `[d]` Due, `[r]` Reviewed
- Select a card to see details in the right pane
- Press `e` to edit a card's topic
- Press `d` to delete a card (press `y` to confirm)
- Press `Escape` to deselect or go back

## Keybindings

### Global

| Key | Action |
|-----|--------|
| `q` | Quit |
| `,` | Open Settings |

### Home Screen

| Key | Action |
|-----|--------|
| `1` | Add Problem |
| `2` | Add Concept |
| `3` | Review Due |
| `b` | Browse Cards |
| `s` | Sync LeetCode |

### Review Screen

| Key | Action |
|-----|--------|
| `n` | Skip card |
| `a` | Rate: Again |
| `h` | Rate: Hard |
| `g` | Rate: Good |
| `e` | Rate: Easy |
| `Escape` | Go back |

### Add Concept Screen

| Key | Action |
|-----|--------|
| `Shift+Tab` | Go back from title to subject |

### Browse Screen

| Key | Action |
|-----|--------|
| `a` | Show all cards |
| `n` | Show new cards |
| `d` | Show due cards / Delete selected |
| `r` | Show reviewed cards |
| `e` | Edit topic of selected card |
| `y` | Confirm delete |
| `Escape` | Deselect / Go back |

## Config

On first launch, the setup wizard guides you through configuration. Config is stored at `~/.config/cram/config`:

```ini
OBSIDIAN_VAULT="$HOME/blog/content"
PROBLEM_FOLDER="Private/Daily/Problems"
LEETCODE_USERNAME="your-leetcode-username"
DESIRED_RETENTION=0.9
THEME="tokyonight"
CARDS_FILE="$HOME/.local/share/cram/cards.json"
```

### Themes

Available themes: `default`, `dracula`, `gruvbox`, `nord`, `tokyonight`, `catppuccin`, `solarized`, `forest`

Change theme via the settings screen (press `,`) or edit config directly.

### Desired Retention

Controls how often you want to recall cards successfully. Range: `0.01` to `1.0`.

- `0.9` (default) — 90% retention, balanced review frequency
- `0.8` — fewer reviews, but more forgetting
- `0.95` — more reviews, but better retention

### Notifications

cram can send desktop notifications when cards are due for review. Requires `dunst` + `dunstify`.

**Setup:**

```bash
cram setup-notifications   # Enable hourly notifications (systemd timer)
cram remove-notifications  # Disable notifications
```

**Config keys:**

```ini
NOTIFY_ENABLED=true
NOTIFY_INTERVAL=3600       # seconds between checks (default: 3600)
```

**How it works:**
- **In-TUI:** When the TUI is open, cram checks for due cards every hour (using `set_interval`)
- **Background:** `setup-notifications` creates a systemd user timer that runs `cram notify` hourly
- **Desktop:** Notifications are sent via `dunstify` (requires `dunst` running)

**Manual test:**

```bash
cram notify   # Send notification now if cards are due
```

## Data Storage

Cards are stored in JSON at:
- `~/.local/share/cram/cards.json` (default, XDG-compliant)
- `~/cram/data/cards.json` (legacy fallback)

Notes are stored in your Obsidian vault as Markdown files with YAML frontmatter.

## FSRS Algorithm

cram uses [FSRS-4.5](https://github.com/open-spaced-repetition/awesome-fsrs) with default parameters trained on 700M+ Anki reviews. It models:

- **Difficulty** (D) — per-card difficulty (1-10)
- **Stability** (S) — days until recall drops to 90%
- **Retrievability** (R) — current probability of recall

This results in 20-30% fewer reviews compared to older algorithms like SM-2.

## Project Structure

```
cram/
├── srs/
│   ├── app.py            # Main TUI app + CLI
│   ├── cards.py          # FSRS-4.5 algorithm + card CRUD
│   ├── config.py         # Config loader
│   ├── editor.py         # Editor detection
│   ├── export.py         # CSV export + Anki import
│   ├── leetcode.py       # LeetCode GraphQL API
│   ├── notify.py         # dunst notifications
│   ├── obsidian.py       # Obsidian vault scanner
│   ├── templates.py      # Markdown note templates
│   ├── theme.py          # Theme system (8 presets)
│   ├── cram.tcss         # Textual CSS styles
│   └── screens/
│       ├── home.py       # Main menu
│       ├── add_problem.py    # Add problem + create new
│       ├── add_concept.py    # Add concept
│       ├── browse.py         # Browse/search all cards
│       ├── editor.py         # In-TUI note editor
│       ├── review.py         # Review due cards
│       ├── rating.py         # Rating widget
│       ├── setup.py          # First-run wizard
│       └── settings.py       # Theme selector + config
├── tests/
├── data/
├── CHANGELOG.md
├── CONTRIBUTING.md
├── Makefile
├── pyproject.toml
├── LICENSE
└── README.md
```

## Testing

```bash
make test
```

## Linting

```bash
make lint     # ruff + mypy
make format   # ruff format
```

## Troubleshooting

**"No editor found"** — Set `$EDITOR` in your shell, or install `nvim`/`vi`.

**"dunstify not found"** — Install `dunst` for desktop notifications, or ignore (cram works without it).

**"LEETCODE_USERNAME not set"** — Run `cram` and go to Settings (`,`) to set it, or add `LEETCODE_USERNAME="yourname"` to `~/.config/cram/config`.

**Sync failed (429)** — LeetCode rate-limiting. Wait a minute and try again.

**No cards due after sync** — Synced cards become due the next day. Create problems manually for immediate review.

**Rating buttons don't appear** — This was a known bug. Update to the latest version.

**Theme not changing** — Press `,` to open Settings, navigate with arrow keys, press `s` to save.

## License

MIT
