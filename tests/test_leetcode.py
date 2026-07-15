"""Tests for srs.leetcode — API calls and sync logic."""

import json
from datetime import datetime, timedelta, timezone
from unittest.mock import MagicMock, patch

from srs.leetcode import (
    LeetCodeAPIError,
    filter_last_24h,
    sync_leetcode,
)


def _make_submission(slug: str, hours_ago: int = 1) -> dict:
    ts = datetime.now(timezone.utc) - timedelta(hours=hours_ago)
    return {
        "id": "123",
        "title": slug.replace("-", " ").title(),
        "titleSlug": slug,
        "timestamp": str(int(ts.timestamp())),
    }


def test_filter_last_24h():
    recent = _make_submission("two-sum", hours_ago=1)
    old = _make_submission("three-sum", hours_ago=25)
    result = filter_last_24h([recent, old])
    assert len(result) == 1
    assert result[0]["titleSlug"] == "two-sum"


def test_filter_last_24h_empty():
    assert filter_last_24h([]) == []


def test_filter_last_24h_bad_timestamp():
    bad = {"titleSlug": "x", "timestamp": "not-a-number"}
    assert filter_last_24h([bad]) == []


def test_sync_deduplicates_by_slug():
    data = {"problem_cards": []}
    sub1 = _make_submission("two-sum", hours_ago=1)
    sub2 = _make_submission("two-sum", hours_ago=2)
    mock_result = {"data": {"recentAcSubmissionList": [sub1, sub2]}}

    with (
        patch("srs.leetcode.graphql_query", return_value=mock_result),
        patch("srs.leetcode.get_problem_tags_batch", return_value={"two-sum": ["Array"]}),
    ):
        count, new = sync_leetcode("testuser", data)
        assert count == 1
        assert len(data["problem_cards"]) == 1


def test_sync_skips_existing():
    data = {"problem_cards": [{"link": "https://leetcode.com/problems/two-sum/", "id": "old"}]}
    sub = _make_submission("two-sum", hours_ago=1)
    mock_result = {"data": {"recentAcSubmissionList": [sub]}}

    with patch("srs.leetcode.graphql_query", return_value=mock_result):
        count, new = sync_leetcode("testuser", data)
        assert count == 0


def test_sync_api_error():
    with patch("srs.leetcode.graphql_query", side_effect=LeetCodeAPIError("network error")):
        try:
            sync_leetcode("testuser", {"problem_cards": []})
            assert False, "Should have raised"
        except LeetCodeAPIError:
            pass


def test_graphql_error_in_response():
    """GraphQL errors in response body should be handled."""
    response_with_errors = {"errors": [{"message": "User not found"}]}
    with patch("srs.leetcode.urlopen") as mock_url:
        mock_resp = MagicMock()
        mock_resp.read.return_value = json.dumps(response_with_errors).encode()
        mock_url.return_value.__enter__ = lambda s: s
        mock_url.return_value.__exit__ = MagicMock(return_value=False)
        mock_url.return_value.read = mock_resp.read
        # The function should not crash, just return the response
        from srs.leetcode import graphql_query

        result = graphql_query("query {}", {})
        assert "errors" in result


def test_get_recent_ac_submissions_graphql_error():
    from srs.leetcode import get_recent_ac_submissions

    mock_result = {"errors": [{"message": "User does not exist"}], "data": None}
    with patch("srs.leetcode.graphql_query", return_value=mock_result):
        try:
            get_recent_ac_submissions("nonexistent")
            assert False, "Should have raised LeetCodeAPIError"
        except LeetCodeAPIError as e:
            assert str(e) == "User does not exist"
