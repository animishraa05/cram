"""LeetCode GraphQL API — fetch recent accepted submissions (last 24h)."""

import json
import time
from datetime import datetime, timedelta, timezone
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


class LeetCodeAPIError(Exception):
    pass


LEETCODE_GRAPHQL = "https://leetcode.com/graphql"
HEADERS = {
    "Content-Type": "application/json",
    "User-Agent": "cram-sync/1.0",
    "Referer": "https://leetcode.com",
}

TOPIC_MAP = {
    "array": "Array",
    "string": "String",
    "hash-table": "Hash Table",
    "dynamic-programming": "Dynamic Programming",
    "math": "Math",
    "sorting": "Sorting",
    "greedy": "Greedy",
    "depth-first-search": "DFS",
    "breadth-first-search": "BFS",
    "tree": "Tree",
    "binary-search": "Binary Search",
    "matrix": "Matrix",
    "two-pointers": "Two Pointers",
    "stack": "Stack",
    "heap-priority-queue": "Heap",
    "graph": "Graph",
    "linked-list": "Linked List",
    "backtracking": "Backtracking",
    "sliding-window": "Sliding Window",
    "union-find": "Union Find",
    "trie": "Trie",
    "bit-manipulation": "Bit Manipulation",
    "monotonic-stack": "Monotonic Stack",
    "segment-tree": "Segment Tree",
    "binary-search-tree": "BST",
    "recursion": "Recursion",
    "queue": "Queue",
    "hashmap": "Hash Map",
    "counting": "Counting",
    "prefix-sum": "Prefix Sum",
}


def graphql_query(query: str, variables: dict, retries: int = 3) -> dict:
    payload = json.dumps({"query": query, "variables": variables}).encode()
    req = Request(LEETCODE_GRAPHQL, data=payload, headers=HEADERS, method="POST")
    last_err: Exception | None = None
    for attempt in range(retries):
        try:
            with urlopen(req, timeout=15) as resp:
                return dict(json.loads(resp.read()))
        except HTTPError as e:
            last_err = e
            if e.code == 429 and attempt < retries - 1:
                time.sleep(2**attempt)
                continue
            raise LeetCodeAPIError(str(e)) from e
        except (json.JSONDecodeError, URLError) as e:
            raise LeetCodeAPIError(str(e)) from e
    raise LeetCodeAPIError(str(last_err))


def get_recent_ac_submissions(username: str, limit: int = 50) -> list[dict]:
    query = """
    query recentAcSubmissions($username: String!, $limit: Int!) {
        recentAcSubmissionList(username: $username, limit: $limit) {
            id
            title
            titleSlug
            timestamp
        }
    }
    """
    result = graphql_query(query, {"username": username, "limit": limit})
    errors = result.get("errors")
    if errors:
        raise LeetCodeAPIError(errors[0].get("message", "GraphQL Error"))
    data = result.get("data") or {}
    submissions = data.get("recentAcSubmissionList", [])
    return submissions if submissions is not None else []


def get_problem_tags(title_slug: str) -> list[str]:
    query = """
    query questionTags($titleSlug: String!) {
        question(titleSlug: $titleSlug) {
            topicTags {
                name
                slug
            }
        }
    }
    """
    result = graphql_query(query, {"titleSlug": title_slug})
    errors = result.get("errors")
    if errors:
        raise LeetCodeAPIError(errors[0].get("message", "GraphQL Error"))
    data = result.get("data") or {}
    question = data.get("question")
    if question:
        tags = question.get("topicTags") or []
        return [t["name"] for t in tags if t and "name" in t]
    return []


def get_problem_tags_batch(slugs: list[str]) -> dict[str, list[str]]:
    """Fetch topic tags for multiple problems one at a time to avoid 429."""
    if not slugs:
        return {}

    tag_map: dict[str, list[str]] = {}
    for slug in slugs:
        try:
            tags = get_problem_tags(slug)
            tag_map[slug] = tags
        except LeetCodeAPIError:
            tag_map[slug] = []
        time.sleep(0.3)
    return tag_map


def filter_last_24h(submissions: list[dict]) -> list[dict]:
    """Filter submissions to only those from the last 24 hours."""
    cutoff = datetime.now(timezone.utc) - timedelta(hours=24)
    filtered = []
    for sub in submissions:
        try:
            ts = datetime.fromtimestamp(int(sub["timestamp"]), tz=timezone.utc)
            if ts >= cutoff:
                filtered.append(sub)
        except (KeyError, ValueError, TypeError):
            pass
    return filtered


def sync_leetcode(username: str, cards_data: dict) -> tuple[int, list[dict]]:
    """Fetch last-24h AC submissions, add new cards to data.

    Returns (new_count, new_cards_list).
    Raises LeetCodeAPIError on network/API failures.
    """
    from srs import config
    from srs.cards import make_card

    submissions = get_recent_ac_submissions(username, limit=50)
    if not submissions:
        return 0, []

    recent = filter_last_24h(submissions)
    seen_slugs: set[str] = set()
    new_slugs: list[str] = []

    for sub in recent:
        slug = sub["titleSlug"]
        if slug in seen_slugs:
            continue

        expected_link = f"https://leetcode.com/problems/{slug}/"
        if any(c.get("link", "") == expected_link for c in cards_data.get("problem_cards", [])):
            seen_slugs.add(slug)
            continue

        seen_slugs.add(slug)
        new_slugs.append(slug)

    if not new_slugs:
        return 0, []

    tag_map = get_problem_tags_batch(new_slugs)
    time.sleep(0.2)

    sub_map = {s["titleSlug"]: s for s in recent}
    new_cards: list[dict] = []
    for slug in new_slugs:
        sub = sub_map[slug]
        topic = (tag_map.get(slug) or ["General"])[0]

        card = make_card(
            "problem",
            sub["title"],
            link=f"https://leetcode.com/problems/{slug}/",
            topic=topic,
            subject="DSA",
            folder=config.problem_folder(),
            filename=f"{slug}.md",
        )
        card["next_review"] = (datetime.now(timezone.utc) + timedelta(days=1)).isoformat()
        cards_data["problem_cards"].append(card)
        new_cards.append(card)

    return len(new_cards), new_cards
