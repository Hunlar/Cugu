from aiogram import BaseMiddleware
from aiogram.types import TelegramObject

from language import detect_language
from storage import get_database


class CinemaMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler,
        event: TelegramObject,
        data: dict,
    ):
        user = data.get("event_from_user")

        data["language"] = detect_language(user)
        data["database"] = get_database()

        return await handler(event, data)
