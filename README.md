# cram

Spaced repetition TUI for programming problems and academic concepts, powered by FSRS-4.5.

cram helps you remember LeetCode problems and study complex concepts using spaced repetition. It optionally syncs your recent LeetCode submissions, can save notes in your Obsidian vault (or in a local notes folder if you prefer), and schedules reviews when the forgetting curve says you should revisit a card.

---

## Key Features

- **LeetCode Integration**: Automatically syncs accepted submissions from the last 24 hours.
- **Obsidian-Optional**: Card notes are saved as standard Markdown files — inside your Obsidian vault if configured, or in a local notes folder (`~/.local/share/cram/notes`) otherwise.
- **FSRS-4.5 Engine**: Powered by the modern Free Spaced Repetition Scheduler, displaying exact recall probabilities and next review intervals (like Anki).
- **Dual-Pane Dashboard TUI**: Full-screen split panes with rounded borders, dynamic title updates, active due card alerts, and stats grids.
- **Flexible Note Editor**: Choose between a native, inline Markdown editor (`TextArea`) built right into the TUI (default), or any external editor you prefer (`nvim`, `vim`, `code`, etc.).
- **Silent Git Auto-Backup**: Automatically commits and pushes note modifications and card logs to your private Git repositories in background threads.
- **Developer-Centric UX**: Standard Vim navigation (`j`/`k`/`o`/`Enter`/`Esc`), hotkeys, and left/right arrow key navigation for horizontal dialog boxes.

---

## Install

### Prerequisites

**Required:**
- Python >= 3.10
- [pipx](https://pipx.pypa.io/stable/)

```bash
# Arch Linux
sudo pacman -S python-pipx

# macOS
brew install pipx

# Debian/Ubuntu
sudo apt install pipx
```

**Optional:**
- `nvim`, `vim`, or any other editor — only needed if you use **external editor mode** (default is **embedded**).
- `dunst` + `dunstify` — for desktop notifications

### Install cram

#### Arch Linux (AUR) — recommended

```bash
yay -S cram-srs-git
```

> This installs the latest git version directly from source via the AUR.

#### From source (any distro)

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

---

## Quick Start

1. Run `cram` in your terminal — the setup wizard will guide you through config creation.
2. Optionally set your Obsidian vault path. If left blank, notes are saved locally at `~/.local/share/cram/notes`.
3. Optionally set your LeetCode username and run **Sync LeetCode** to import solves.
4. Select **Review Queue** to start studying cards.

---

## Usage

```bash
cram                  # Open TUI home screen dashboard
cram add-problem      # Open problem picker
cram add-concept      # Open concept form
cram review           # Open review queue
cram browse           # Browse all cards
cram sync             # CLI: fetch last-24h LeetCode submissions
cram sync-concepts    # CLI: scan and import concepts from Obsidian vault
cram export           # CLI: export card registry as CSV to stdout
cram import FILE      # CLI: import cards from Anki TSV file
cram notify           # CLI: send dunst notification for due cards
cram setup-notifications  # Enable hourly desktop notifications (systemd user timer)
cram remove-notifications # Disable hourly notifications
```

---

## TUI Walkthrough

### 1. Command Dashboard (Home Screen)
The home screen splits the view into a navigation menu on the left and a telemetry dashboard on the right:
- **Alerts**: Displays review counts due in muted red or a success catchup message in muted green.
- **Card Stats**: Lists total cards, cards reviewed, new cards, and average review intervals.
- **Focus Areas**: Showcases your top 3 subject topics needing attention.
- **Navigation**: Move menu items using `j`/`k` and select with `o`/`Enter`.

### 2. Adding Problems & Concepts
- **Sync**: Synced LeetCode problems automatically import with topic tags (like `Array`, `Hash Table`) and are scheduled for review the next day.
- **Manual Problem**: Select `[+] Create new problem...` in the problem picker. Fill out the title and links.
- **Manual Concept**: Enter the subject folder (e.g., `OS`) and the concept title (e.g., `Virtual Memory`).
- **Editor & Rate**: Your editor will launch. After saving and exiting, you immediately rate your recall.

### 3. Review Queue
- **Split Layout**: Left pane lists due cards. Selecting a card immediately loads its Markdown note in the right pane.
- **Recall Probability**: Displays the exact calculated probability of recall (e.g., `Recall Probability: 86.4%`) in the preview footer.
- **Dynamic Titles**: The border title of the preview pane automatically changes to display the active note's name (e.g., ` preview: Two Sum [Array] `).
- **Skip Card**: Press `n` while focused on the card list to skip a card and defer its review.

### 4. Spaced Repetition Rating Dialog
When rating card recall, a horizontal widget bar displays predicted FSRS intervals directly on the buttons (e.g., `Good [g] (12d)`):

| Key | Rating | When to use |
|-----|--------|-------------|
| `a` | Again | Complete blackout — couldn't recall at all (Next: ~1d) |
| `h` | Hard | Significant effort to recall (Next: ~4d) |
| `g` | Good | Some thought needed, but got it (Next: ~12d) |
| `e` | Easy | Instant recall, no effort (Next: ~28d) |

- **Navigation**: Press left and right arrow keys to shift focus across the rating options, or press `a`/`h`/`g`/`e` for instant keyboard ratings. Press `Esc` to cancel.

### 5. Settings Configuration Screen
Press `,` (comma) from anywhere to open Settings:
- **Left Column**: Forms to modify vault path, problem folders, LeetCode username, desired retention, notifications, and editor mode.
- **Right Column**: Scrollable Theme Selector list (`j`/`k` to navigate) and live theme color swatch previews.
- **Shortcuts**: Press `Ctrl+h` to focus the config input forms. Press `Ctrl+l` to focus the theme selection list. Press `Ctrl+s` to save and apply settings.

### 6. Browse Cards
Select **Browse Cards** on the main menu (or run `cram browse`) to search and manage your cards:
- **Search**: Press `/` to focus the search box. Type to filter by title or topic.
- **Edit Topic**: Press `e` to change the topic/category of the selected card.
- **Delete Card**: Press `d` to initiate deletion, then press `y` to confirm (or `Esc` to cancel).

---

## Feature Details

### 📝 Embedded Note Editor Mode
You can edit notes inline without suspending the TUI or launching an external terminal editor:
1. Go to Settings (press `,`).
2. Set **Editor Mode** to `embedded` (default is `external`).
3. Press `Ctrl+s` to save.
When creating or editing notes, a premium inline Markdown text editor (`TextArea`) will occupy the viewport. Press **`Ctrl+s`** to save your text and exit, or **`Esc`** to cancel.

### 💾 Git Auto-Sync / Auto-Backup
cram will silently back up your Obsidian notes and card logs in a background thread:
- If your Obsidian vault directory contains a `.git` folder, cram runs a background git commit/push routine whenever you create a note or rate a card.
- If your `cards.json` directory is a Git repository, cram will sync that folder too.
- Pushes are sent to your git remote origin server (if configured). Status updates are shown as non-intrusive TUI notifications.

> [!IMPORTANT]
> Since git auto-sync runs in the background, your repository must be configured to push without interactive password prompts (e.g., using SSH keys or a credential helper).

### 📂 Importing and Exporting
* **Anki TSV Import**: `cram import FILE` imports cards from an Anki-compatible Tab-Separated Values (TSV) export file.
  * **Format**: Lines must be structured as `FrontText\tBackText\tTags` (or at least `FrontText\tBackText`).
  * The first tag will be used as the topic (defaulting to `General`), and the card will be added as a `problem` card.
* **CSV Export**: `cram export` exports your card list in CSV format: `type, title, topic, link, subject, review_count, interval, next_review`.

### 🔍 Concept Scanning (`sync-concepts`)
`cram sync-concepts` recursively scans your Obsidian vault for notes matching concept cards.
* Only markdown files (`.md`) containing **`type: concept`** in their YAML frontmatter will be imported.
* Example concept frontmatter:
  ```yaml
  ---
  title: "Virtual Memory"
  type: concept
  subject: "Operating Systems"
  ---
  ```

---

## Config

Config is stored at `~/.config/cram/config`:

```ini
OBSIDIAN_VAULT="$HOME/blog/content"  # Optional — leave empty for local notes
PROBLEM_FOLDER="Private/Daily/Problems"
LEETCODE_USERNAME="your-leetcode-username"  # Optional
DESIRED_RETENTION=0.9
THEME="tokyonight"
EDITOR_MODE="embedded"  # 'embedded' (default) or 'external'
EDITOR=""               # External editor command — only used when EDITOR_MODE=external
CARDS_FILE="$HOME/.local/share/cram/cards.json"

# Notification Settings
NOTIFY_ENABLED="true"
NOTIFY_INTERVAL=3600
MAX_ITEMS=8
URGENCY="normal"
TIMEOUT=0
```

### Themes
Supported: `default`, `dracula`, `gruvbox`, `nord`, `tokyonight`, `catppuccin`, `solarized`, `forest`

### Desired Retention
Sets the target probability of successful recall (from `0.01` to `1.0`).
- `0.9` (default) — balanced review intervals.
- `0.85` — longer intervals, slightly more forgetting.
- `0.95` — shorter intervals, very high retention.

### Notifications
- **NOTIFY_ENABLED**: Toggle background hourly notifications (`true`/`false`).
- **NOTIFY_INTERVAL**: Refresh time in seconds (minimum `60`).
- **MAX_ITEMS**: Limit the number of due cards listed in a single notification pop-up.
- **URGENCY**: Dunst urgency level (`low`, `normal`, `critical`).
- **TIMEOUT**: Dunst notification display time in milliseconds (`0` for persistent, until clicked).

---

## Project Structure

```
cram/
├── srs/
│   ├── app.py            # Main TUI app + CLI
│   ├── cards.py          # FSRS-4.5 scheduling engine
│   ├── config.py         # Config loader
│   ├── editor.py         # External editor detection
│   ├── git_sync.py       # Git Auto-Sync background runner
│   ├── export.py         # CSV Export + Anki TSV Import
│   ├── leetcode.py       # LeetCode GraphQL Client
│   ├── notify.py         # dunst desktop notifications
│   ├── obsidian.py       # Obsidian vault scanner
│   ├── templates.py      # Markdown templates
│   ├── theme.py          # Color themes (8 presets)
│   ├── cram.tcss         # Textual CSS styles
│   └── screens/
│       ├── home.py       # Dashboard Menu screen
│       ├── add_problem.py    # Problem picker + creator
│       ├── add_concept.py    # Concept form screen
│       ├── browse.py         # Card search & edit browser
│       ├── editor.py         # In-TUI TextArea editor
│       ├── review.py         # Review Queue screen
│       ├── rating_dialog.py  # Recall rating modal
│       ├── confirm.py        # Yes/no modal
│       ├── settings.py       # Theme selector + config forms
│       └── setup.py          # Setup wizard
├── tests/                # PyTest suite
├── CHANGELOG.md
├── CONTRIBUTING.md
├── Makefile
├── pyproject.toml
└── README.md
```

---

## Troubleshooting

**"No editor found"** — Set `$EDITOR` in your shell, or go to settings (`,`) and set **Editor Mode** to `embedded`.

**"dunstify not found"** — Install `dunst` for desktop notifications. The TUI will still run perfectly without it.

**Theme not changing** — Open settings (`,`), scroll the theme list, and ensure you press **`Ctrl+s`** to save.

**Sync failed (429 / LeetCode API Error)** — LeetCode rate-limiting or username not found. Wait a minute and try again.

---

## License

MIT
