from aiogram.types import User

from i18n import translate


SUPPORTED_LANGUAGES = {
    "tr", "en", "de", "fr", "es", "ar",
    "ru", "uk", "az", "fa", "it", "pt",
    "nl", "pl", "ja", "ko", "zh", "hi",
}


def detect_language(user: User | None) -> str:
    if not user or not user.language_code:
        return "tr"

    language = user.language_code.lower().split("-")[0]

    if language not in SUPPORTED_LANGUAGES:
        return "en"

    return language


async def localize(
    text: str,
    user: User | None,
) -> str:
    language = detect_language(user)

    if language == "tr":
        return text

    return await translate(text, language)
