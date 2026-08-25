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
        image.get("relative_path", "")
    ])

    normalized_text = normalize(searchable_text)
    compact_text = compact(searchable_text)

    normalized_query = normalize(query)
    compact_query = compact(query)
    tokens = tokenize(query)

    if not normalized_query:
        return 0

    score = 0

    # Exact phrase match
    if kmp_contains(normalized_text, normalized_query):
        score += 100

    # No-space match
    if compact_query and kmp_contains(compact_text, compact_query):
        score += 90

    # Token matching
    matched_tokens = 0

    for token in tokens:
        if kmp_contains(normalized_text, token):
            matched_tokens += 1
            score += 30

    # For multi-word queries, require all tokens.
    if len(tokens) > 1 and matched_tokens < len(tokens):
        return 0

    # For single-word queries, require that one word.
    if len(tokens) == 1 and matched_tokens == 0 and score == 0:
        return 0

    # Bonus when all tokens match
    if tokens and matched_tokens == len(tokens):
        score += 50

    return score