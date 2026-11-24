
"""GROUP CINEMA - HD Film Cehennemi authorized catalog integration."""

import os
import logging
from typing import Any

import httpx

logger = logging.getLogger(__name__)

HDCEHENNEMI_CATALOG_URL = os.getenv(
    "HDCEHENNEMI_CATALOG_URL", ""
).strip()

HDCEHENNEMI_API_KEY = os.getenv(
    "HDCEHENNEMI_API_KEY", ""
).strip()

TIMEOUT = 20


def normalize_item(item: dict[str, Any]) -> dict[str, Any] | None:
    """Normalize a catalog item."""

    title = (
        item.get("title")
        or item.get("name")
        or item.get("displayName")
    )

    if not title:
        return None

    return {
        "id": str(item.get("id") or item.get("contentId") or title),
        "source": "hd_film_cehennemi",
        "title": str(title),
        "description": str(item.get("description") or ""),
        "content_type": str(
            item.get("type") or item.get("contentType") or "unknown"
        ),
        "thumbnail": item.get("thumbnail") or item.get("poster"),
        "metadata": item,
    }


async def search_catalog(query: str) -> list[dict[str, Any]]:
    """Search an authorized HD Film Cehennemi catalog endpoint."""

    query = query.strip()

    if not query:
        return []

    if not HDCEHENNEMI_CATALOG_URL:
        raise RuntimeError(
            "HDCEHENNEMI_CATALOG_URL is not configured."
        )

    headers = {
        "Accept": "application/json",
        "User-Agent": "GROUP-CINEMA/1.0",
    }

    if HDCEHENNEMI_API_KEY:
        headers["Authorization"] = (
            f"Bearer {HDCEHENNEMI_API_KEY}"
        )

    try:
        async with httpx.AsyncClient(
            timeout=TIMEOUT,
            follow_redirects=True,
        ) as client:
            response = await client.get(
                HDCEHENNEMI_CATALOG_URL,
                params={"q": query},
                headers=headers,
            )

            response.raise_for_status()
            payload = response.json()

    except httpx.HTTPError:
        logger.exception("HD Film Cehennemi catalog request failed")
        raise RuntimeError(
            "HD Film Cehennemi catalog could not be reached."
        )

    if isinstance(payload, list):
        items = payload

    elif isinstance(payload, dict):
        items = (
            payload.get("results")
            or payload.get("items")
            or payload.get("data")
            or []
        )

        if isinstance(items, dict):
            items = (
                items.get("results")
                or items.get("items")
                or []
            )

    else:
        return []

    if not isinstance(items, list):
        return []

    results = []

    for item in items:
        if not isinstance(item, dict):
            continue

        normalized = normalize_item(item)

        if normalized:
            results.append(normalized)

    return results[:20]
          
