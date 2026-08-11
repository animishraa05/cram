import sys
import json
from datetime import datetime, timedelta, timezone
from urllib.request import Request, urlopen

sys.path.append("/home/ani/cram")
from srs import config
from srs.leetcode import get_problem_tags_batch
from srs.cards import make_card

def load_cards_json():
    path = config.cards_file()
    if path.exists():
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"problem_cards": [], "concept_cards": []}

def save_cards_json(data):
    path = config.cards_file()
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)

def fetch_all_ac_slugs(cookie: str):
    url = "https://leetcode.com/api/problems/algorithms/"
    headers = {
        "Cookie": f"LEETCODE_SESSION={cookie}",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
    }
    req = Request(url, headers=headers)
    with urlopen(req) as resp:
        data = json.loads(resp.read())
    
    ac_slugs_and_titles = []
    for pair in data.get("stat_status_pairs", []):
        if pair.get("status") == "ac":
            title = pair["stat"]["question__title"]
            slug = pair["stat"]["question__title_slug"]
            ac_slugs_and_titles.append((slug, title))
            
    return ac_slugs_and_titles

def main():
    cookie = input("Paste your LEETCODE_SESSION cookie: ").strip()
    if not cookie:
        print("Cookie is required!")
        return

    print("Fetching all AC problems from LeetCode...")
    try:
        ac_problems = fetch_all_ac_slugs(cookie)
    except Exception as e:
        print(f"Failed to fetch from LeetCode. Is your session cookie correct? Error: {e}")
        return

    print(f"Found {len(ac_problems)} accepted problems.")

    cards_data = load_cards_json()
    existing_links = {c.get("link", "") for c in cards_data.get("problem_cards", [])}
    
    new_problems = []
    for slug, title in ac_problems:
        expected_link = f"https://leetcode.com/problems/{slug}/"
        if expected_link not in existing_links:
            new_problems.append((slug, title))
            
    print(f"Found {len(new_problems)} new problems to add to Cram.")
    if not new_problems:
        return

    slugs_to_fetch = [slug for slug, _ in new_problems]
    print("Fetching problem tags from GraphQL API (this might take a bit)...")
    
    tag_map = {}
    chunk_size = 20
    for i in range(0, len(slugs_to_fetch), chunk_size):
        chunk = slugs_to_fetch[i:i+chunk_size]
        print(f"Fetching tags for chunk {i//chunk_size + 1}/{(len(slugs_to_fetch) - 1)//chunk_size + 1}...")
        chunk_map = get_problem_tags_batch(chunk)
        tag_map.update(chunk_map)

    for slug, title in new_problems:
        topic = (tag_map.get(slug) or ["General"])[0]
        card = make_card(
            "problem",
            title,
            link=f"https://leetcode.com/problems/{slug}/",
            topic=topic,
            subject="DSA",
            folder=config.problem_folder(),
            filename=f"{slug}.md",
        )
        card["next_review"] = (datetime.now(timezone.utc) + timedelta(days=1)).isoformat()
        cards_data.setdefault("problem_cards", []).append(card)

    save_cards_json(cards_data)
    print(f"Successfully added {len(new_problems)} new problem cards to Cram!")

if __name__ == '__main__':
    main()
