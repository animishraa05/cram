"""Tests for srs.cards — FSRS algorithm + card CRUD."""

from datetime import datetime, timedelta, timezone

from srs.cards import (
    compute_stats,
    find_card_by_id,
    find_card_by_title,
    get_due_cards,
    initial_difficulty,
    initial_stability,
    load_cards,
    make_card,
    next_interval,
    retrievability,
    save_cards,
    update_card,
)


def test_make_card_defaults():
    card = make_card("problem", "Two Sum", link="https://leetcode.com/two-sum/", topic="Array")
    assert card["type"] == "problem"
    assert card["title"] == "Two Sum"
    assert card["link"] == "https://leetcode.com/two-sum/"
    assert card["topic"] == "Array"
    assert card["stability"] == 1.0
    assert card["difficulty"] == 5.0
    assert card["interval"] == 1
    assert card["repetition"] == 0
    assert card["lapses"] == 0
    assert card["reviews"] == []
    assert "id" in card
    assert len(card["id"]) > 0


def test_make_card_concept():
    card = make_card("concept", "TCP", subject="Networking")
    assert card["type"] == "concept"
    assert card["subject"] == "Networking"


def test_update_card_good_grows_stability():
    card = make_card("problem", "Test")
    old_stability = card["stability"]
    update_card(card, 3)  # Good
    assert card["stability"] > old_stability
    assert card["interval"] >= 1
    assert card["repetition"] == 1
    assert card["lapses"] == 0


def test_update_card_easy_grows_more():
    card1 = make_card("problem", "Test1")
    card2 = make_card("problem", "Test2")
    update_card(card1, 3)  # Good
    update_card(card2, 4)  # Easy
    assert card2["stability"] > card1["stability"]


def test_update_card_again_increases_lapses():
    card = make_card("problem", "Test")
    update_card(card, 3)  # Good first
    update_card(card, 1)  # Again
    assert card["lapses"] == 1
    assert card["repetition"] == 0


def test_update_card_sets_next_review():
    card = make_card("problem", "Test")
    update_card(card, 3)
    assert card["next_review"] is not None
    nr = datetime.fromisoformat(card["next_review"].replace("Z", "+00:00"))
    assert nr > datetime.now(timezone.utc)


def test_update_card_stores_review_history():
    card = make_card("problem", "Test")
    update_card(card, 3)
    assert len(card["reviews"]) == 1
    assert card["reviews"][0]["rating"] == 3
    assert "reviewed_at" in card["reviews"][0]


def test_elapsed_days_computed():
    card = make_card("problem", "Test")
    # Simulate old review
    old_time = (datetime.now(timezone.utc) - timedelta(days=3)).isoformat()
    card["last_reviewed"] = old_time
    update_card(card, 3)
    # Should have used ~3 days elapsed for retrievability
    assert card["stability"] > 1.0


def test_retrievability_at_zero():
    r = retrievability(0, 1.0)
    assert r == 1.0  # At t=0, R=1


def test_retrievability_decreases():
    r1 = retrievability(1, 1.0)
    r2 = retrievability(5, 1.0)
    assert r1 > r2


def test_retrievability_zero_stability():
    r = retrievability(1, 0)
    assert r == 0.0


def test_next_interval_positive():
    interval = next_interval(5.0, 0.9)
    assert interval >= 1.0


def test_initial_stability():
    assert initial_stability(1) == 0.4  # Again
    assert initial_stability(3) == 2.4  # Good
    assert initial_stability(4) == 5.8  # Easy


def test_initial_difficulty():
    d = initial_difficulty(3)
    assert 1.0 <= d <= 10.0


def test_find_card_by_id():
    data = {
        "problem_cards": [make_card("problem", "A")],
        "concept_cards": [make_card("concept", "B")],
    }
    card_id = data["problem_cards"][0]["id"]
    found = find_card_by_id(data, card_id)
    assert found is not None
    assert found["title"] == "A"


def test_find_card_by_id_not_found():
    data = {"problem_cards": [], "concept_cards": []}
    assert find_card_by_id(data, "nonexistent") is None


def test_find_card_by_title():
    data = {"problem_cards": [make_card("problem", "Two Sum")], "concept_cards": []}
    found = find_card_by_title(data, "two sum", "problem")
    assert found is not None
    assert found["title"] == "Two Sum"


def test_find_card_by_title_not_found():
    data = {"problem_cards": [], "concept_cards": []}
    assert find_card_by_title(data, "X", "problem") is None


def test_get_due_cards():
    data = {"problem_cards": [], "concept_cards": []}
    card1 = make_card("problem", "Due")
    card1["next_review"] = (datetime.now(timezone.utc) - timedelta(hours=1)).isoformat()
    card2 = make_card("problem", "Not Due")
    card2["next_review"] = (datetime.now(timezone.utc) + timedelta(days=10)).isoformat()
    data["problem_cards"] = [card1, card2]
    due = get_due_cards(data)
    assert len(due) == 1
    assert due[0]["title"] == "Due"


def test_get_due_cards_empty():
    data = {"problem_cards": [], "concept_cards": []}
    assert get_due_cards(data) == []


def test_save_and_load_cards(tmp_path):
    path = tmp_path / "cards.json"
    data = {"problem_cards": [make_card("problem", "Test")], "concept_cards": []}
    save_cards(path, data)
    loaded = load_cards(path)
    assert len(loaded["problem_cards"]) == 1
    assert loaded["problem_cards"][0]["title"] == "Test"


def test_load_cards_nonexistent(tmp_path):
    path = tmp_path / "nonexistent.json"
    loaded = load_cards(path)
    assert loaded == {"problem_cards": [], "concept_cards": []}


def test_update_card_hard_grade():
    card = make_card("problem", "Test")
    update_card(card, 2)  # Hard
    assert card["stability"] == 0.6  # initial_stability(2) = 0.6
    assert card["repetition"] == 1


def test_update_card_invalid_grade():
    card = make_card("problem", "Test")
    try:
        update_card(card, 0)
        assert False, "Should have raised ValueError"
    except ValueError:
        pass
    try:
        update_card(card, 5)
        assert False, "Should have raised ValueError"
    except ValueError:
        pass


def test_initial_stability_invalid_grade():
    try:
        initial_stability(0)
        assert False, "Should have raised ValueError"
    except ValueError:
        pass


def test_initial_difficulty_invalid_grade():
    try:
        initial_difficulty(5)
        assert False, "Should have raised ValueError"
    except ValueError:
        pass


def test_review_count_increments():
    card = make_card("problem", "Test")
    assert card["review_count"] == 0
    update_card(card, 3)
    assert card["review_count"] == 1
    update_card(card, 3)
    assert card["review_count"] == 2


def test_review_count_not_reset_on_again():
    card = make_card("problem", "Test")
    update_card(card, 3)
    assert card["review_count"] == 1
    update_card(card, 1)  # Again
    assert card["review_count"] == 2


def test_reviews_capped_at_100():
    card = make_card("problem", "Test")
    for _ in range(120):
        update_card(card, 3)
    assert len(card["reviews"]) == 100


def test_make_card_has_review_count():
    card = make_card("problem", "Test")
    assert "review_count" in card
    assert card["review_count"] == 0


def test_make_card_no_ease_factor():
    card = make_card("problem", "Test")
    assert "ease_factor" not in card


def test_find_card_by_title_concept():
    data = {"problem_cards": [], "concept_cards": [make_card("concept", "TCP")]}
    found = find_card_by_title(data, "tcp", "concept")
    assert found is not None
    assert found["title"] == "TCP"


def test_compute_stats_empty():
    data = {"problem_cards": [], "concept_cards": []}
    stats = compute_stats(data)
    assert stats["total"] == 0


def test_compute_stats():
    data = {
        "problem_cards": [
            make_card("problem", "A", topic="Array"),
            make_card("problem", "B", topic="Array"),
        ],
        "concept_cards": [make_card("concept", "C", topic="Networking")],
    }
    stats = compute_stats(data)
    assert stats["total"] == 3
    assert stats["new"] == 3
    assert stats["topics"]["Array"] == 2
    assert stats["topics"]["Networking"] == 1


def test_load_cards_corrupt_backup(tmp_path):
    path = tmp_path / "cards.json"
    path.write_text("not valid json {{{")
    loaded = load_cards(path)
    assert loaded == {"problem_cards": [], "concept_cards": []}
    assert (tmp_path / "cards.json.corrupt").exists()


def test_predict_next_intervals():
    from srs.cards import predict_next_intervals

    card = make_card("problem", "Test")
    intervals = predict_next_intervals(card)
    assert len(intervals) == 4
    for grade in (1, 2, 3, 4):
        assert intervals[grade] >= 1


def test_current_retrievability():
    from srs.cards import current_retrievability

    card = make_card("problem", "Test")
    assert current_retrievability(card) == 100.0
    # After a review, retrievability decay can be computed
    update_card(card, 3)  # Good
    # Instantly after review, retrievability is high
    assert current_retrievability(card) > 90.0
