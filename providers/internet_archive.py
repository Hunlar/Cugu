"""Internet Archive catalog integration for openly licensed video items.

Only items with an explicit public-domain or permissive Creative Commons
license are returned. Rights metadata is supplied by uploaders and is not
an independent legal guarantee; review each item before public exhibition.
"""

import asyncio
import logging
from urllib.parse import quote
from typing import Any

import httpx

logger = logging.getLogger(__name__)

BASE_URL = "https://archive.org"
TIMEOUT = 25
SEARCH_LIMIT = 15
ALLOWED_LICENSE_MARKERS = (
    "creativecommons.org/publicdomain/zero/",
    "creativecommons.org/publicdomain/mark/",
    "creativecommons.org/licenses/by/",
    "creativecommons.org/licenses/by-sa/",
)
PUBLIC_DOMAIN_RIGHTS_MARKERS = (
    "public domain",
    "public-domain",
    "no known copyright restrictions",
)


def _text(value: Any) -> str:
    if isinstance(value, list):
        return " ".join(str(part) for part in value if part is not None).strip()
    if value is None:
        return ""
    return str(value).strip()


def _license_details(metadata: dict[str, Any]) -> tuple[bool, str, str]:
    license_url = _text(metadata.get("licenseurl"))
    rights = _text(metadata.get("rights"))
    combined = f"{license_url} {rights}".lower()

    allowed = (
        any(marker in license_url.lower() for marker in ALLOWED_LICENSE_MARKERS)
        or any(marker in rights.lower() for marker in PUBLIC_DOMAIN_RIGHTS_MARKERS)
    )

    if "public domain" in combined or "public-domain" in combined:
        label = "Public Domain"
    elif "publicdomain/zero" in combined:
        label = "CC0"
    elif "publicdomain/mark" in combined:
        label = "Public Domain Mark"
    elif "licenses/by-sa/" in combined:
        label = "CC BY-SA"
    elif "licenses/by/" in combined:
        label = "CC BY"
    else:
        label = "Lisans bilgisi doğrulanamadı"

    return allowed, label, license_url


def _select_mp4(files: list[dict[str, Any]]) -> dict[str, Any] | None:
    candidates = []

    for file_info in files:
        if not isinstance(file_info, dict):
            continue

        name = _text(file_info.get("name"))
        if not name.lower().endswith(".mp4"):
            continue

        source = _text(file_info.get("source")).lower()
        if source and source != "original":
            continue

        if _text(file_info.get("private")).lower() in {"true", "1", "yes"}:
            continue

        try:
            size = int(file_info.get("size") or 0)
        except (TypeError, ValueError):
            size = 0

        if size <= 0:
            continue

        candidates.append((size, name, file_info))

    if not candidates:
        return None

    candidates.sort(key=lambda item: item[0], reverse=True)
    return candidates[0][2]


async def _fetch_item(
    client: httpx.AsyncClient,
    identifier: str,
    title: str,
) -> dict[str, Any] | None:
    response = await client.get(f"{BASE_URL}/metadata/{quote(identifier, safe='')}")
    response.raise_for_status()
    payload = response.json()

    metadata = payload.get("metadata") or {}
    if not isinstance(metadata, dict):
        return None

    allowed, license_label, license_url = _license_details(metadata)
    if not allowed:
        return None

    file_info = _select_mp4(payload.get("files") or [])
    if not file_info:
        return None

    filename = _text(file_info.get("name"))
    encoded_id = quote(identifier, safe="")
    media_url = (
        f"{BASE_URL}/download/{encoded_id}/"
        f"{quote(filename, safe='')}"
    )

    return {
        "id": identifier,
        "source": "internet_archive",
        "title": _text(metadata.get("title")) or title or identifier,
        "description": _text(metadata.get("description"))[:700],
        "content_type": "movie",
        "thumbnail": f"{BASE_URL}/services/img/{encoded_id}",
        "media_url": media_url,
        "license_url": license_url,
        "license_label": license_label,
        "rights": _text(metadata.get("rights"))[:500],
        "creator": _text(metadata.get("creator") or metadata.get("contributor")),
        "item_page": f"{BASE_URL}/details/{encoded_id}",
        "metadata": {
            "identifier": identifier,
            "filename": filename,
            "size": int(file_info.get("size") or 0),
            "format": _text(file_info.get("format")),
            "license_url": license_url,
            "license_label": license_label,
        },
    }


async def search_catalog(query: str) -> list[dict[str, Any]]:
    """Find playable, explicitly licensed movie files on Internet Archive."""
    query = query.strip()
    if len(query) < 2:
        return []

    escaped = query.replace("\\", "\\\\").replace('"', '\\"')
    params = [
        ("q", f'mediatype:movies AND "{escaped}"'),
        ("fl[]", "identifier"),
        ("fl[]", "title"),
        ("rows", str(SEARCH_LIMIT)),
        ("page", "1"),
        ("output", "json"),
    ]

    headers = {
        "Accept": "application/json",
        "User-Agent": "GROUP-CINEMA/1.0 (Internet Archive catalog search)",
    }

    try:
        async with httpx.AsyncClient(
            timeout=TIMEOUT,
            follow_redirects=True,
            headers=headers,
        ) as client:
            response = await client.get(
                f"{BASE_URL}/advancedsearch.php",
                params=params,
            )
            response.raise_for_status()
            payload = response.json()

            docs = (payload.get("response") or {}).get("docs") or []
            semaphore = asyncio.Semaphore(5)

            async def load_one(doc: dict[str, Any]):
                identifier = _text(doc.get("identifier"))
                if not identifier:
                    return None
                async with semaphore:
                    try:
                        return await _fetch_item(
                            client,
                            identifier,
                            _text(doc.get("title")),
                        )
                    except (httpx.HTTPError, ValueError, TypeError, KeyError):
                        logger.warning(
                            "Could not inspect Internet Archive item %s",
                            identifier,
                            exc_info=True,
                        )
                        return None

            items = await asyncio.gather(
                *(load_one(doc) for doc in docs if isinstance(doc, dict))
            )

    except (httpx.HTTPError, ValueError) as exc:
        logger.exception("Internet Archive search failed")
        raise RuntimeError(
            "Internet Archive kataloğuna şu anda ulaşılamıyor."
        ) from exc

    return [item for item in items if item][:10]
