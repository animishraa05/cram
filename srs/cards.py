"""cards.json CRUD + FSRS-4.5 spaced repetition algorithm."""

import json
import math
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path

# FSRS-4.5 default parameters (17 weights)
# Trained on ~700M reviews from Anki users
DEFAULT_W = [
    0.4,    # w0: initial stability for Again
    0.6,    # w1: initial stability for Hard
    2.4,    # w2: initial stability for Good
    5.8,    # w3: initial stability for Easy
    4.93,   # w4: difficulty after Again
    0.94,   # w5: difficulty after Hard
    0.86,   # w6: difficulty after Good
    0.01,   # w7: difficulty after Easy
    1.49,   # w8: stability increase factor
    0.14,   # w9: stability difficulty decay
    0.94,   # w10: stability retrievability decay
    2.18,   # w11: post-lapse stability base
    0.05,   # w12: post-lapse difficulty decay
    0.34,   # w13: post-lapse stability recovery
    1.26,   # w14: post-lapse retrievability decay
    0.29,   # w15: hard penalty
    2.61,   # w16: easy bonus
]

# FSRS-4.5 forgetting curve constants
DECAY = -0.5
FACTOR = 0.9 ** (1 / DECAY) - 1  # ≈ 0.2345679


def retrievability(elapsed_days: float, stability: float) -> float:
    """R(t, S) = (1 + FACTOR * t / S) ^ DECAY"""
    if stability <= 0:
        return 0.0
    return (1 + FACTOR * elapsed_days / stability) ** DECAY


def next_interval(stability: float, desired_retention: float = 0.9) -> float:
    """Calculate interval from stability at desired retention."""
    if stability <= 0:
        return 1.0
    interval = stability / FACTOR * (desired_retention ** (1 / DECAY) - 1)
    return max(1.0, round(interval))


def next_difficulty(difficulty: float, grade: int, w: list[float] | None = None) -> float:
    """Update difficulty after a review. Grade: 1=Again, 2=Hard, 3=Good, 4=Easy."""
    if w is None:
        w = DEFAULT_W
    q = 5 - grade  # invert: Again=4, Hard=3, Good=2, Easy=1
    new_d = difficulty - w[6] * (q - 1)
    return max(1.0, min(10.0, new_d))


def next_stability_after_recall(
    difficulty: float,
    stability: float,
    retrievability: float,
    grade: int,
    w: list[float] | None = None,
) -> float:
    """Stability after successful recall (Hard/Good/Easy)."""
    if w is None:
        w = DEFAULT_W
    r = max(retrievability, 0.01)
    s_inc = (
        math.exp(w[8])
        * (11 - difficulty)
        * stability ** (-w[9])
        * (math.exp(w[10] * (1 - r)) - 1)
        * w[15] ** (1 if grade == 2 else 0)
        * w[16] ** (1 if grade == 4 else 0)
    )
    return stability * (1 + s_inc)


def next_stability_after_forget(
    difficulty: float,
    stability: float,
    retrievability: float,
    w: list[float] | None = None,
) -> float:
    """Stability after forgetting (Again)."""
    if w is None:
        w = DEFAULT_W
    r = max(retrievability, 0.01)
    return w[11] * difficulty ** (-w[12]) * ((stability + 1) ** w[13] - 1) * math.exp(w[14] * (1 - r))


def initial_stability(grade: int, w: list[float] | None = None) -> float:
    """Initial stability for a new card based on first rating."""
    if w is None:
        w = DEFAULT_W
    return w[grade - 1]


def initial_difficulty(grade: int, w: list[float] | None = None) -> float:
    """Initial difficulty for a new card."""
    if w is None:
        w = DEFAULT_W
    return max(1.0, min(10.0, w[4] - w[5] * (grade - 1)))


def _compute_elapsed_days(card: dict, now: datetime) -> float:
    """Compute days elapsed since last review."""
    last_reviewed = card.get("last_reviewed")
    if not last_reviewed:
        return 1.0
    try:
        last_dt = datetime.fromisoformat(last_reviewed.replace("Z", "+00:00"))
        delta = (now - last_dt).total_seconds() / 86400
        return max(0.0, delta)
    except Exception:
        return 1.0


def update_card(card: dict, grade: int, desired_retention: float = 0.9) -> dict:
    """Apply FSRS-4.5 update to a card after a review.

    Grade: 1=Again, 2=Hard, 3=Good, 4=Easy
    """
    now = datetime.now(timezone.utc)

    if card.get("repetition", 0) == 0 and card.get("interval", 1) == 1:
        # New card — first review
        card["difficulty"] = initial_difficulty(grade)
        card["stability"] = initial_stability(grade)
        card["repetition"] = 1 if grade > 1 else 0
    else:
        elapsed = _compute_elapsed_days(card, now)
        r = retrievability(elapsed, card["stability"])
        card["difficulty"] = next_difficulty(card["difficulty"], grade)

        if grade == 1:
            # Forgot
            card["stability"] = next_stability_after_forget(
                card["difficulty"], card["stability"], r
            )
            card["repetition"] = 0
            card["lapses"] = card.get("lapses", 0) + 1
        else:
            # Recalled
            card["stability"] = next_stability_after_recall(
                card["difficulty"], card["stability"], r, grade
            )
            card["repetition"] = card.get("repetition", 0) + 1

    card["interval"] = next_interval(card["stability"], desired_retention)
    card["ease_factor"] = max(1.3, card["stability"] / card["interval"]) if card["interval"] > 0 else 2.5
    card["next_review"] = (now + timedelta(days=card["interval"])).isoformat()

    # Store review in history
    reviews = card.setdefault("reviews", [])
    prev_reviewed = card.get("last_reviewed", "")
    if prev_reviewed:
        delta = (now - datetime.fromisoformat(prev_reviewed.replace("Z", "+00:00"))).days
    else:
        delta = 0
    reviews.append({
        "rating": grade,
        "reviewed_at": now.isoformat(),
        "delta_days": max(1, delta),
    })

    card["last_reviewed"] = now.isoformat()

    return card


# ── Card CRUD ──────────────────────────────────────────────────────

def load_cards(path: Path) -> dict:
    if path.exists():
        return json.loads(path.read_text())
    return {"concept_cards": [], "problem_cards": []}


def save_cards(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2))


def make_card(
    card_type: str,
    title: str,
    *,
    link: str = "",
    topic: str = "",
    subject: str = "",
    folder: str = "",
    filename: str = "",
) -> dict:
    now = datetime.now(timezone.utc)
    return {
        "id": str(uuid.uuid4()),
        "type": card_type,
        "title": title,
        "subject": subject,
        "folder": folder,
        "filename": filename,
        "link": link,
        "topic": topic,
        "created": now.strftime("%Y-%m-%d"),
        "last_reviewed": now.isoformat(),
        "next_review": now.isoformat(),
        "repetition": 0,
        "ease_factor": 2.5,
        "interval": 1,
        "difficulty": 5.0,
        "stability": 1.0,
        "lapses": 0,
        "reviews": [],
    }


def find_card_by_title(data: dict, title: str, card_type: str = "problem") -> dict | None:
    key = "problem_cards" if card_type == "problem" else "concept_cards"
    for c in data.get(key, []):
        if c.get("title", "").lower() == title.lower():
            return c
    return None


def find_card_by_id(data: dict, card_id: str) -> dict | None:
    for key in ("problem_cards", "concept_cards"):
        for c in data.get(key, []):
            if c.get("id") == card_id:
                return c
    return None


def get_due_cards(data: dict) -> list[dict]:
    now = datetime.now(timezone.utc)
    due = []
    for key in ("problem_cards", "concept_cards"):
        for c in data.get(key, []):
            try:
                nr = datetime.fromisoformat(c["next_review"].replace("Z", "+00:00"))
                if nr <= now:
                    due.append(c)
            except Exception:
                pass
    return due
