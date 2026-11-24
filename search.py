from typing import Any

from providers import search_catalog


class CatalogSearchError(Exception):
    pass


async def search_content(
    source: str,
    query: str,
    database: Any = None,
) -> list[dict]:
    query = query.strip()

    if source not in ("puhutv", "hd_film_cehennemi", "internet_archive"):
        raise CatalogSearchError("Geçersiz yayın kaynağı.")

    if len(query) < 2:
        raise CatalogSearchError("Arama için en az 2 karakter gir.")

    try:
        results = await search_catalog(source, query)
    except Exception as exc:
        raise CatalogSearchError(
            f"Yayın kaynağı aranamadı: {exc}"
        ) from exc

    cleaned_results = []

    for item in results:
        if not isinstance(item, dict):
            continue

        item_id = str(item.get("id") or "").strip()
        title = str(item.get("title") or "").strip()

        if not item_id or not title:
            continue

        content_id = f"{source}:{item_id}"

        content = {
            "id": content_id,
            "source": source,
            "title": title,
            "description": str(item.get("description") or ""),
            "content_type": str(item.get("content_type") or "unknown"),
            "thumbnail": item.get("thumbnail"),
            "media_url": item.get("media_url"),
            "license_url": item.get("license_url"),
            "license_label": item.get("license_label"),
            "rights": item.get("rights"),
            "creator": item.get("creator"),
            "item_page": item.get("item_page"),
            "metadata": item.get("metadata") or {},
        }

        if database is not None:
            try:
                await database.save_content(
                    content_id=content_id,
                    source=source,
                    title=title,
                    content_type=content["content_type"],
                    metadata=content,
                )
            except Exception as exc:
                raise CatalogSearchError(
                    f"İçerik veritabanına kaydedilemedi: {exc}"
                ) from exc

        cleaned_results.append(content)

    return cleaned_results[:20]
