from brain.domain.services.hashtags import extract_hashtags, normalize_hashtag_texts


def test_normalize_hashtag_texts_cleans_and_deduplicates_preserving_order():
    # setup: prepare mixed hashtags with spaces, case differences, and duplicates
    raw_hashtags = [" #Work ", "ideas", "#IDEAS", "  ", "#work", "#AI"]

    # action: normalize hashtag list
    normalized = normalize_hashtag_texts(texts=raw_hashtags)

    # check: hashtags are lowercased, stripped, deduplicated, and ordered by first appearance
    assert normalized == ["work", "ideas", "ai"]


def test_normalize_hashtag_texts_ignores_empty_values():
    # setup: prepare only empty-like hashtag values
    raw_hashtags = ["", "   ", "#", " # "]

    # action: normalize hashtag list
    normalized = normalize_hashtag_texts(texts=raw_hashtags)

    # check: empty values are removed
    assert normalized == []


def test_extract_hashtags_returns_empty_for_none_or_empty_text():
    # setup: prepare empty text inputs
    empty_text = ""
    none_text = None

    # action: extract hashtags from both values
    from_empty = extract_hashtags(text=empty_text)
    from_none = extract_hashtags(text=none_text)

    # check: both inputs produce no hashtags
    assert from_empty == []
    assert from_none == []


def test_extract_hashtags_extracts_and_normalizes_from_text():
    # setup: prepare text with repeated hashtags and punctuation
    text = "Plan #Work, ship #AI. Repeat #work and keep #ml_2"

    # action: extract hashtags from text
    hashtags = extract_hashtags(text=text)

    # check: hashtags are normalized, deduplicated, and punctuation is excluded
    assert hashtags == ["work", "ai", "ml_2"]


def test_extract_hashtags_respects_word_boundaries():
    # setup: prepare text where one hashtag is attached to a word
    text = "email#ignored but #included and value#also_ignored"

    # action: extract hashtags from text
    hashtags = extract_hashtags(text=text)

    # check: only standalone hashtags are captured
    assert hashtags == ["included"]
