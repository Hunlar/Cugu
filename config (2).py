"""GROUP CINEMA - central configuration.

Set these values as Heroku Config Vars (or in a local .env file).
Never commit real tokens, API hashes, or session strings to GitHub.
"""

import os
from dataclasses import dataclass
from typing import Optional

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass


def _get_int(name: str, default: Optional[int] = None) -> Optional[int]:
    value = os.getenv(name)
    if value is None or value.strip() == "":
        return default
    try:
        return int(value)
    except ValueError as exc:
        raise ValueError(f"{name} must be an integer") from exc


def _get_bool(name: str, default: bool = False) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


@dataclass(frozen=True)
class Settings:
    # Telegram bot
    bot_token: str = os.getenv("BOT_TOKEN", "").strip()
    api_id: Optional[int] = _get_int("API_ID")
    api_hash: str = os.getenv("API_HASH", "").strip()

    # User account used by the authorized group-call streaming client
    string_session: str = os.getenv("STRING_SESSION", "").strip()

    # Database
    database_url: str = os.getenv("DATABASE_URL", "").strip()

    # Optional Google Cloud Translation API key
    google_translate_api_key: str = os.getenv("GOOGLE_TRANSLATE_API_KEY", "").strip()

    # Private Telegram group/channel used for authorized media storage and logs
    storage_chat_id: Optional[int] = _get_int("STORAGE_CHAT_ID")
    log_chat_id: Optional[int] = _get_int("LOG_CHAT_ID")

    # Project links
    support_group: str = os.getenv(
        "SUPPORT_GROUP", "https://t.me/ozturkordusu"
    ).strip()
    support_channel: str = os.getenv(
        "SUPPORT_CHANNEL", "https://t.me/sancakmain"
    ).strip()
    developer_url: str = os.getenv(
        "DEVELOPER_URL", "https://t.me/byatillaozturk"
    ).strip()

    # Defaults and runtime
    default_language: str = os.getenv("DEFAULT_LANGUAGE", "tr").strip().lower()
    log_level: str = os.getenv("LOG_LEVEL", "INFO").strip().upper()
    debug: bool = _get_bool("DEBUG", False)


settings = Settings()


def validate_bot_config() -> None:
    """Validate the minimum settings needed to start the Telegram bot."""
    missing = []
    if not settings.bot_token:
        missing.append("BOT_TOKEN")
    if missing:
        raise RuntimeError(
            "Missing required Heroku Config Vars: " + ", ".join(missing)
        )


def validate_streaming_config() -> None:
    """Validate settings needed when enabling the user-account streaming worker."""
    missing = []
    if settings.api_id is None:
        missing.append("API_ID")
    if not settings.api_hash:
        missing.append("API_HASH")
    if not settings.string_session:
        missing.append("STRING_SESSION")
    if missing:
        raise RuntimeError(
            "Missing streaming Config Vars: " + ", ".join(missing)
        )
