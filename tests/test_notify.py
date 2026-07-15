"""Tests for srs.notify — notification logic."""

from unittest.mock import patch

from srs.notify import notify_due


def test_notify_due_no_dunstify():
    with patch("srs.notify.shutil.which", return_value=None):
        notify_due()  # Should not crash


def test_notify_due_no_cards():
    mock_data = {"problem_cards": [], "concept_cards": []}
    with (
        patch("srs.notify.shutil.which", return_value="dunstify"),
        patch("srs.notify.cards.load_cards", return_value=mock_data),
        patch("srs.notify.config.cards_file"),
        patch("srs.notify.config.load_config", return_value={}),
    ):
        notify_due()  # Should not crash


def test_notify_due_with_cards():
    from datetime import datetime, timedelta, timezone

    card = {
        "title": "Two Sum",
        "type": "problem",
        "topic": "Array",
        "next_review": (datetime.now(timezone.utc) - timedelta(hours=1)).isoformat(),
    }
    mock_data = {"problem_cards": [card], "concept_cards": []}
    with (
        patch("srs.notify.shutil.which", return_value="dunstify"),
        patch("srs.notify.cards.load_cards", return_value=mock_data),
        patch("srs.notify.config.cards_file"),
        patch("srs.notify.config.load_config", return_value={}),
        patch("srs.notify.send_notification") as mock_send,
    ):
        notify_due()
        mock_send.assert_called_once()
        args = mock_send.call_args
        assert "1 due" in args[0][0]
