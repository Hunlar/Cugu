
"""GROUP CINEMA - PuhuTV authorized catalog integration."""

import os
import logging
from typing import Any

import httpx

logger = logging.getLogger(__name__)

PUHUTV_CATALOG_URL = os.getenv("PUHUTV_CATALOG_URL", "").strip()
PUHUTV_API_KEY = os.getenv("PUHUTV_API_KEY", "").strip()

TIMEOUT = 20


def normalize_item(item: dict[str, Any]) -> dict[str, Any] | None:
    """Convert a provider catalog item into GROUP CINEMA format."""

    title = (
        item.get("title")
        or item.get("name")
        or item.get("displayName")
    )

    if not title:
        return None

    return {
        "id": str(item.get("id") or item.get("contentId") or title),
        "source": "puhutv",
        "title": str(title),
        "description": str(item.get("description") or ""),
        "content_type": str(
            item.get("type") or item.get("contentType") or "unknown"
        ),
        "thumbnail": item.get("thumbnail") or item.get("poster"),
        "metadata": item,
    }


async def search_catalog(query: str) -> list[dict[str, Any]]:
    """Search PuhuTV's authorized catalog endpoint."""

    query = query.strip()

    if not query:
        return []

    if not PUHUTV_CATALOG_URL:
        raise RuntimeError(
            "PUHUTV_CATALOG_URL is not configured. "
            "Configure an authorized catalog endpoint first."
        )

    headers = {
        "Accept": "application/json",
        "User-Agent": "GROUP-CINEMA/1.0",
    }

    if PUHUTV_API_KEY:
        headers["Authorization"] = f"Bearer {PUHUTV_API_KEY}"

    params = {"q": query}

    try:
        async with httpx.AsyncClient(
            timeout=TIMEOUT,
            follow_redirects=True,
        ) as client:
            response = await client.get(
                PUHUTV_CATALOG_URL,
                params=params,
                headers=headers,
            )
            response.raise_for_status()
            payload = response.json()

    except httpx.HTTPError:
        logger.exception("PuhuTV catalog request failed")
        raise RuntimeError("PuhuTV catalog could not be reached.")

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
            items = items.get("results") or items.get("items") or []

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
