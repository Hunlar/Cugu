from pyrogram import Client
from pyrogram.types import Message


class TelegramStorage:
    def __init__(self, client: Client, storage_chat_id: int):
        self.client = client
        self.storage_chat_id = storage_chat_id

    async def save_media(self, media_url: str) -> Message:
        if not media_url.startswith(("http://", "https://")):
            raise ValueError("Geçersiz medya adresi.")

        message = await self.client.send_video(
            chat_id=self.storage_chat_id,
            video=media_url,
            caption="GROUP CINEMA | Medya arşivi",
        )

        return message

    async def save_audio(self, media_url: str) -> Message:
        if not media_url.startswith(("http://", "https://")):
            raise ValueError("Geçersiz medya adresi.")

        message = await self.client.send_audio(
            chat_id=self.storage_chat_id,
            audio=media_url,
            caption="GROUP CINEMA | Ses arşivi",
        )

        return message

    async def get_saved_media(self, message_id: int) -> Message:
        return await self.client.get_messages(
            chat_id=self.storage_chat_id,
            message_ids=message_id,
        )

    async def delete_saved_media(self, message_id: int):
        await self.client.delete_messages(
            chat_id=self.storage_chat_id,
            message_ids=message_id,
        )
