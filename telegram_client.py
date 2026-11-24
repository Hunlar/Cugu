from pyrogram import Client

from config import settings


class TelegramUserClient:
    def __init__(self):
        if not settings.api_id or not settings.api_hash:
            raise RuntimeError("API_ID veya API_HASH eksik.")

        if not settings.string_session:
            raise RuntimeError("STRING_SESSION eksik.")

        self.client = Client(
            name="group_cinema",
            api_id=settings.api_id,
            api_hash=settings.api_hash,
            session_string=settings.string_session,
            in_memory=True,
        )

    async def start(self):
        await self.client.start()

        if not await self.client.get_me():
            raise RuntimeError("Telegram hesabı doğrulanamadı.")

        return self.client

    async def stop(self):
        if self.client.is_connected:
            await self.client.stop()

    def get_client(self):
        return self.client
