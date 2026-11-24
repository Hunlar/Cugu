
"""GROUP CINEMA automatic translation system."""

import asyncio
import logging
import httpx

from config import settings

logger = logging.getLogger(__name__)

TRANSLATE_URL = "https://translation.googleapis.com/language/translate/v2"

_cache = {}
_cache_lock = asyncio.Lock()


def normalize_language(language_code=None):
    """Telegram language code normalization."""
    if not language_code:
        return settings.default_language or "tr"

    code = language_code.strip().replace("_", "-").split("-")[0].lower()

    if code.isalpha() and 2 <= len(code) <= 3:
        return code

    return settings.default_language or "tr"


async def translate(text, target_language=None):
    """Translate Turkish text into the user's language."""

    target = normalize_language(target_language)

    if not text or target == "tr":
        return text

    api_key = settings.google_translate_api_key

    if not api_key:
        return text

    cache_key = (target, text)

    async with _cache_lock:
        if cache_key in _cache:
            return _cache[cache_key]

    payload = {
        "q": text,
        "target": target,
        "source": "tr",
        "format": "text"
    }

    try:
        async with httpx.AsyncClient(timeout=15) as client:
            response = await client.post(
                TRANSLATE_URL,
                params={"key": api_key},
                data=payload
            )

            response.raise_for_status()

            result = response.json()
            translated = result["data"]["translations"][0]["translatedText"]

    except Exception:
        logger.exception("Translation error")
        return text

    async with _cache_lock:
        _cache[cache_key] = translated

    return translated


async def tr(text, user_or_language=None):
    """Translate according to Telegram user's language."""

    if isinstance(user_or_language, str):
        language = user_or_language
    else:
        language = getattr(
            user_or_language,
            "language_code",
            None
        )

    return await translate(text, language)


async def translate_many(texts, target_language=None):
    """Translate multiple messages."""

    return await asyncio.gather(
        *[
            translate(text, target_language)
            for text in texts
        ]
  )
  
