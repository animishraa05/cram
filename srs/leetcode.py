"""LeetCode GraphQL API — fetch recent accepted submissions (last 24h)."""

import json
from datetime import datetime, timezone, timedelta
from urllib.request import Request, urlopen
from urllib.error import URLError

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


def graphql_query(query: str, variables: dict) -> dict:
    payload = json.dumps({"query": query, "variables": variables}).encode()
    req = Request(LEETCODE_GRAPHQL, data=payload, headers=HEADERS, method="POST")
    try:
        with urlopen(req, timeout=15) as resp:
            return json.loads(resp.read())
    except URLError:
        return {}


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
    return result.get("data", {}).get("recentAcSubmissionList", [])


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
    question = result.get("data", {}).get("question")
    if question:
        return [t["name"] for t in question.get("topicTags", [])]
    return []


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
    """
    from srs.cards import make_card
    from srs import config

    submissions = get_recent_ac_submissions(username, limit=50)
    if not submissions:
        return 0, []

    recent = filter_last_24h(submissions)
    seen_slugs: set[str] = set()
    new_cards: list[dict] = []

    for sub in recent:
        slug = sub["titleSlug"]
        if slug in seen_slugs:
            continue

        # Skip if already in cards.json
        already = False
        for c in cards_data.get("problem_cards", []):
            if slug in c.get("link", ""):
                already = True
                break
        if already:
            seen_slugs.add(slug)
            continue

        seen_slugs.add(slug)
        tags = get_problem_tags(slug)
        topic = tags[0] if tags else "General"

        card = make_card(
            "problem",
            sub["title"],
            link=f"https://leetcode.com/problems/{slug}/",
            topic=topic,
            subject="DSA",
            folder=config.problem_folder(),
            filename=f"{slug}.md",
        )
        # Set next_review to 1 day from now (new card)
        card["next_review"] = (datetime.now(timezone.utc) + timedelta(days=1)).isoformat()
        cards_data["problem_cards"].append(card)
        new_cards.append(card)

    return len(new_cards), new_cards
