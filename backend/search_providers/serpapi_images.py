import os
from typing import Any

import httpx


SERPAPI_URL = "https://serpapi.com/search"


class ExternalSearchError(Exception):
    """Raised when SerpApi image search cannot be completed."""


async def search_google_images(
    query: str,
    page: int = 0,
    safe_search: str = "active",
) -> list[dict[str, Any]]:
    api_key = os.getenv("SERPAPI_API_KEY")

    if not api_key:
        raise ExternalSearchError("SERPAPI_API_KEY is not configured.")

    cleaned_query = query.strip()

    if not cleaned_query:
        return []

    params = {
        "engine": "google_images",
        "q": cleaned_query,
        "api_key": api_key,
        "ijn": page,
        "safe": safe_search,
        "no_cache": "false",
    }

    try:
        async with httpx.AsyncClient(timeout=25.0) as client:
            response = await client.get(SERPAPI_URL, params=params)
            response.raise_for_status()

    except httpx.TimeoutException as error:
        raise ExternalSearchError(
            "The online image search timed out."
        ) from error

    except httpx.HTTPStatusError as error:
        raise ExternalSearchError(
            f"SerpApi returned HTTP {error.response.status_code}."
        ) from error

    except httpx.RequestError as error:
        raise ExternalSearchError(
            "The online image search request could not be completed."
        ) from error

    payload = response.json()

    if payload.get("error"):
        raise ExternalSearchError(str(payload["error"]))

    normalized_results: list[dict[str, Any]] = []

    for index, result in enumerate(payload.get("images_results", [])):
        original_url = result.get("original")
        thumbnail_url = result.get("thumbnail")

        if not original_url or not thumbnail_url:
            continue

        position = result.get("position", index)

        normalized_results.append({
            "id": f"serpapi-{page}-{position}",
            "title": result.get("title", "Untitled image"),
            "source": "serpapi",
            "thumbnail_url": thumbnail_url,
            "full_url": original_url,
            "source_page": result.get("link"),
            "source_name": result.get("source"),
            "width": result.get("original_width"),
            "height": result.get("original_height"),
        })

    return normalized_results