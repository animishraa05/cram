"""Markdown note templates for concepts and problems."""

import re
from datetime import datetime, timezone


def concept_template(title: str, subject: str) -> str:
    safe_title = title.replace("\\", "\\\\").replace('"', '\\"')
    safe_subject = subject.replace("\\", "\\\\").replace('"', '\\"')
    date = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    return f"""---
title: "{safe_title}"
type: concept
subject: "{safe_subject}"
tags: []
created: {date}
---

## What is it?
<!-- One-liner plain English. How would you explain it to someone with zero background? -->


## Intuition
<!-- Why does this exist? What problem does it solve? What is the mental model? -->


## How it works
<!-- Step-by-step breakdown. Numbered list. One sentence per step. -->


## Example
<!-- ONE concrete example. Input -> process -> output. Show it working. -->


## Common Mistakes
<!-- What trips people up? What is counterintuitive? What breaks? -->


## Connections
<!-- Related topics, concepts, or tools. Link using [[wikilink]]. -->


## Self-Test
<!-- 3 questions to verify understanding. Cover: what, why, edge case. -->
1.
2.
3.

## Notes
<!-- Anything else. Insights from real usage. Links to docs. -->

"""


def problem_template(title: str, link: str, topic: str) -> str:
    safe_title = title.replace("\\", "\\\\").replace('"', '\\"')
    safe_link = link.replace("\\", "\\\\").replace('"', '\\"')
    safe_topic = topic.replace("\\", "\\\\").replace('"', '\\"')
    date = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    return f"""---
title: "{safe_title}"
link: "{safe_link}"
topic: "{safe_topic}"
type: problem
created: {date}
---

## Approach
<!-- Strategy. What pattern/technique applies and why? -->


## Code
<!-- Your solution. Language of choice. -->


## Complexity
<!-- Time: O(...) Space: O(...) and justification. -->


## Edge Cases
<!-- Inputs that break the naive solution. -->


## Notes
<!-- Lessons learned. What would you do differently? -->

"""


def sanitize_filename(title: str) -> str:
    name = title.lower().strip()
    name = re.sub(r"[^\w\s-]", "", name)
    name = re.sub(r"[\s]+", " ", name).strip()
    name = name.replace(" ", "-")
    return name[:200] if name else "untitled"
