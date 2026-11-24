from aiogram.filters.callback_data import CallbackData


class CinemaCallback(CallbackData, prefix="gc"):
    action: str
    item_id: str = "none"


class SourceCallback(CallbackData, prefix="source"):
    source: str


class PlaybackCallback(CallbackData, prefix="play"):
    action: str
    chat_id: int = 0
