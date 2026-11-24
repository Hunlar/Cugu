from telethon import TelegramClient
from telethon.sessions import StringSession

from config import settings


class TelegramUserClient:
    def __init__(self):
        if not settings.api_id or not settings.api_hash:
            raise RuntimeError("API_ID ve API_HASH eksik.")

        if not settings.string_session:
            raise RuntimeError("STRING_SESSION eksik.")

        self.client = TelegramClient(
            StringSession(settings.string_session),
            settings.api_id,
            settings.api_hash,
        )

    async def start(self):
        await self.client.start()

        if not await self.client.is_user_authorized():
            raise RuntimeError("Telegram kullanıcı hesabı yetkilendirilmemiş.")

    async def stop(self):
        if self.client.is_connected():
            await self.client.disconnect()

    async def get_client(self):
        return self.client
