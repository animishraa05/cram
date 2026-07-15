"""cards.json CRUD + FSRS-4.5 spaced repetition algorithm."""

import json
import math
import os
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path

# FSRS-4.5 default parameters (17 weights)
# Trained on ~700M reviews from Anki users
DEFAULT_W = [
    0.4,  # w0: initial stability for Again
    0.6,  # w1: initial stability for Hard
    2.4,  # w2: initial stability for Good
    5.8,  # w3: initial stability for Easy
    4.93,  # w4: difficulty after Again
    0.94,  # w5: difficulty after Hard
    0.86,  # w6: difficulty after Good
    0.01,  # w7: difficulty after Easy
    1.49,  # w8: stability increase factor
    0.14,  # w9: stability difficulty decay
    0.94,  # w10: stability retrievability decay
    2.18,  # w11: post-lapse stability base
    0.05,  # w12: post-lapse difficulty decay
    0.34,  # w13: post-lapse stability recovery
    1.26,  # w14: post-lapse retrievability decay
    0.29,  # w15: hard penalty
    2.61,  # w16: easy bonus
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
    return (
        w[11] * difficulty ** (-w[12]) * ((stability + 1) ** w[13] - 1) * math.exp(w[14] * (1 - r))
    )


def initial_stability(grade: int, w: list[float] | None = None) -> float:
    """Initial stability for a new card based on first rating."""
    if not 1 <= grade <= 4:
        raise ValueError(f"Grade must be 1-4, got {grade}")
    if w is None:
        w = DEFAULT_W
    return w[grade - 1]


def initial_difficulty(grade: int, w: list[float] | None = None) -> float:
    """Initial difficulty for a new card."""
    if not 1 <= grade <= 4:
        raise ValueError(f"Grade must be 1-4, got {grade}")
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
    if not 1 <= grade <= 4:
        raise ValueError(f"Grade must be 1-4, got {grade}")

    now = datetime.now(timezone.utc)

    if card.get("review_count", 0) == 0:
        card["difficulty"] = initial_difficulty(grade)
        card["stability"] = initial_stability(grade)
        card["repetition"] = 1 if grade > 1 else 0
    else:
        elapsed = _compute_elapsed_days(card, now)
        r = retrievability(elapsed, card["stability"])
        card["difficulty"] = next_difficulty(card["difficulty"], grade)

        if grade == 1:
            card["stability"] = next_stability_after_forget(
                card["difficulty"], card["stability"], r
            )
            card["repetition"] = 0
            card["lapses"] = card.get("lapses", 0) + 1
        else:
            card["stability"] = next_stability_after_recall(
                card["difficulty"], card["stability"], r, grade
            )
            card["repetition"] = card.get("repetition", 0) + 1

    card["review_count"] = card.get("review_count", 0) + 1
    card["interval"] = next_interval(card["stability"], desired_retention)
    card["next_review"] = (now + timedelta(days=card["interval"])).isoformat()

    # Store review in history
    reviews = card.setdefault("reviews", [])
    prev_reviewed = card.get("last_reviewed", "")
    delta = 0
    if prev_reviewed:
        try:
            delta = (now - datetime.fromisoformat(prev_reviewed.replace("Z", "+00:00"))).days
        except (ValueError, TypeError):
            delta = 0
    reviews.append(
        {
            "rating": grade,
            "reviewed_at": now.isoformat(),
            "delta_days": max(0, delta),
        }
    )
    card["reviews"] = reviews[-100:]

    card["last_reviewed"] = now.isoformat()

    return card


# ── Card CRUD ──────────────────────────────────────────────────────


def load_cards(path: Path) -> dict:
    if path.exists():
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as e:
            import logging

            logger = logging.getLogger("cram")
            logger.warning("Corrupted cards.json (%s), backing up and starting fresh", e)
            backup = path.with_suffix(".json.corrupt")
            try:
                import shutil

                shutil.copy2(path, backup)
            except OSError:
                pass
            path.write_text('{"concept_cards": [], "problem_cards": []}', encoding="utf-8")
    return {"concept_cards": [], "problem_cards": []}


def save_cards(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(".tmp")
    try:
        tmp.write_text(json.dumps(data, indent=2), encoding="utf-8")
        os.replace(tmp, path)
    except OSError:
        try:
            tmp.unlink(missing_ok=True)
        except OSError:
            pass
        raise


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
        "review_count": 0,
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
            nr_str = c.get("next_review")
            if not nr_str:
                due.append(c)
                continue
            try:
                nr = datetime.fromisoformat(nr_str.replace("Z", "+00:00"))
                if nr <= now:
                    due.append(c)
            except (ValueError, TypeError):
                due.append(c)
    return due


def compute_stats(data: dict) -> dict:
    """Compute summary statistics for the dashboard."""

    all_cards = []
    for key in ("problem_cards", "concept_cards"):
        all_cards.extend(data.get(key, []))

    total = len(all_cards)
    if total == 0:
        return {"total": 0, "due": 0, "new": 0, "reviewed": 0, "topics": {}, "avg_interval": 0.0}

    due = get_due_cards(data)
    new = sum(1 for c in all_cards if c.get("review_count", 0) == 0)
    reviewed = total - new

    topics: dict[str, int] = {}
    total_interval = 0
    for c in all_cards:
        topic = c.get("topic", "General")
        topics[topic] = topics.get(topic, 0) + 1
        total_interval += c.get("interval", 1)

    return {
        "total": total,
        "due": len(due),
        "new": new,
        "reviewed": reviewed,
        "topics": dict(sorted(topics.items(), key=lambda x: -x[1])[:8]),
        "avg_interval": round(total_interval / total, 1),
    }


def predict_next_intervals(card: dict, desired_retention: float = 0.9) -> dict[int, int]:
    """Calculate the next interval (in days) for each grade (1-4) without mutating the card."""
    now = datetime.now(timezone.utc)
    intervals = {}
    for grade in (1, 2, 3, 4):
        card_copy = {
            "review_count": card.get("review_count", 0),
            "difficulty": card.get("difficulty", 5.0),
            "stability": card.get("stability", 1.0),
            "repetition": card.get("repetition", 0),
            "lapses": card.get("lapses", 0),
            "last_reviewed": card.get("last_reviewed"),
        }

        if card_copy["review_count"] == 0:
            stability = initial_stability(grade)
        else:
            elapsed = _compute_elapsed_days(card_copy, now)
            r = retrievability(elapsed, card_copy["stability"])
            diff = next_difficulty(card_copy["difficulty"], grade)
            if grade == 1:
                stability = next_stability_after_forget(diff, card_copy["stability"], r)
            else:
                stability = next_stability_after_recall(diff, card_copy["stability"], r, grade)

        intervals[grade] = int(next_interval(stability, desired_retention))
    return intervals


def current_retrievability(card: dict) -> float:
    """Calculate current retrievability (probability of recall) as a percentage (0.0 to 100.0)."""
    if card.get("review_count", 0) == 0:
        return 100.0
    now = datetime.now(timezone.utc)
    elapsed = _compute_elapsed_days(card, now)
    return retrievability(elapsed, card.get("stability", 1.0)) * 100.0
