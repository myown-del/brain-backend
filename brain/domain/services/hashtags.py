import re


HASHTAG_PATTERN = re.compile(r"(?<!\w)#([A-Za-z0-9_]+)")


def normalize_hashtag_texts(texts: list[str]) -> list[str]:
    seen: set[str] = set()
    normalized: list[str] = []
    for text in texts:
        cleaned = text.strip()
        if cleaned.startswith("#"):
            cleaned = cleaned[1:]
        cleaned = cleaned.lower().strip()
        if not cleaned or cleaned in seen:
            continue
        seen.add(cleaned)
        normalized.append(cleaned)
    return normalized


def extract_hashtags(text: str | None) -> list[str]:
    if not text:
        return []
    raw_matches = HASHTAG_PATTERN.findall(text)
    return normalize_hashtag_texts(raw_matches)
