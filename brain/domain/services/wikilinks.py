import re

from brain.domain.value_objects import LinkInterval


# Example 1: [[Child]] -> ["Child"]
# Example 2: [[Child|alias]] -> ["Child"]
WIKILINK_PATTERN = re.compile(r"\[\[([^\[\]\n]+)\]\]")


def extract_link_targets(text: str) -> list[str]:
    """Return unique wikilink targets extracted from the supplied text."""
    if not text:
        return []

    raw_titles = WIKILINK_PATTERN.findall(text)
    seen: set[str] = set()
    targets: list[str] = []
    for title in raw_titles:
        cleaned = title.strip()
        if "|" in cleaned:
            cleaned = cleaned.split("|", 1)[0].strip()
        if cleaned and cleaned not in seen:
            seen.add(cleaned)
            targets.append(cleaned)
    return targets


def extract_wikilinks(text: str) -> list[str]:
    """Backward-compatible alias that returns the list of link targets."""
    return extract_link_targets(text)


def extract_link_intervals(text: str) -> list[LinkInterval]:
    """
    Returns a list of LinkInterval(start, end) for every wikilink found.
    The interval is [start, end), consistent with Python slicing.
    """
    if not text:
        return []

    intervals = []
    for match in WIKILINK_PATTERN.finditer(text):
        start, end = match.span()
        intervals.append(LinkInterval(start=start, end=end))
    return intervals
