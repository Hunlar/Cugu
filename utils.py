import re
from html import escape
from typing import Any


def clean_text(value: Any, max_length: int = 500) -> str:
    if value is None:
        return ""

    text = re.sub(r"\s+", " ", str(value)).strip()
    return text[:max_length]


def safe_html(value: Any) -> str:
    return escape(clean_text(value))


def content_type_label(content_type: str) -> str:
    labels = {
        "movie": "🎬 Film",
        "series": "📺 Dizi",
        "episode": "🎞 Bölüm",
        "live": "🔴 Canlı yayın",
        "unknown": "📁 İçerik",
    }

    return labels.get(content_type.lower(), "📁 İçerik")


def format_content(item: dict) -> str:
    title = safe_html(item.get("title", "İsimsiz içerik"))
    description = safe_html(item.get("description", ""))
    content_type = content_type_label(
        str(item.get("content_type", "unknown"))
    )

    result = f"<b>{title}</b>\n\n{content_type}"

    if description:
        result += f"\n\n{description}"

    return result
