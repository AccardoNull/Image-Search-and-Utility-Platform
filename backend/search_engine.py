import re
from algorithms.kmp import kmp_contains

def normalize(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", " ", text.lower()).strip()

def compact(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", "", text.lower())

def tokenize(query: str) -> list[str]:
    return normalize(query).split()

def score_image(image: dict, query: str) -> int:
    searchable_text = " ".join([
        image.get("filename", ""),
        " ".join(image.get("tags", [])),
        image.get("description", ""),
        image.get("filepath", "")
    ])

    normalized_text = normalize(searchable_text)
    compact_text = compact(searchable_text)
    normalized_query = normalize(query)
    compact_query = compact(query)
    tokens = tokenize(query)

    score = 0

    # Exact phrase match
    if kmp_contains(normalized_text, normalized_query):
        score += 100

    # No-space match
    if kmp_contains(compact_text, compact_query):
        score += 70

    # Unordered token match
    matched_tokens = 0
    for token in tokens:
        if kmp_contains(normalized_text, token):
            matched_tokens += 1
            score += 30

    # Require at least one token match
    if tokens and matched_tokens == 0:
        return 0

    # Bonus if all tokens match
    if tokens and matched_tokens == len(tokens):
        score += 50

    return score