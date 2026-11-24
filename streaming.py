from pyrogram import Client
from pytgcalls import PyTgCalls
from pytgcalls.types import MediaStream


class StreamingManager:
    def __init__(self, client: Client):
        self.client = client
        self.calls = PyTgCalls(client)
        self.active_streams = {}

    async def start(self):
        await self.calls.start()

    async def play(self, chat_id: int, media_url: str):
        if not media_url.startswith(("http://", "https://")):
            raise ValueError("Geçersiz medya adresi.")

        stream = MediaStream(media_url)
        await self.calls.play(chat_id, stream)

        self.active_streams[chat_id] = media_url

    async def stop(self, chat_id: int):
        await self.calls.leave_call(chat_id)
        self.active_streams.pop(chat_id, None)

    def is_playing(self, chat_id: int) -> bool:
        return chat_id in self.active_streams
