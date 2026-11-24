from typing import Optional

from pyrogram import Client
from pytgcalls import PyTgCalls
from pytgcalls.types import MediaStream
from pytgcalls.types.input_stream import AudioPiped, VideoPiped


class StreamingManager:
    def __init__(self, client: Client):
        self.client = client
        self.calls = PyTgCalls(client)
        self.active_streams: dict[int, dict] = {}

    async def start(self):
        await self.calls.start()

    async def play(
        self,
        chat_id: int,
        media_url: str,
        video: bool = True,
    ):
        if not media_url.startswith(("http://", "https://")):
            raise ValueError("Geçersiz yayın adresi.")

        if video:
            stream = MediaStream(
                media_url,
                video_flags=MediaStream.FLAG再,
            )
        else:
            stream = MediaStream(media_url)

        await self.calls.play(chat_id, stream)

        self.active_streams[chat_id] = {
            "media_url": media_url,
            "video": video,
        }

    async def stop(self, chat_id: int):
        await self.calls.leave_call(chat_id)
        self.active_streams.pop(chat_id, None)

    async def is_playing(self, chat_id: int) -> bool:
        return chat_id in self.active_streams

    def get_stream(self, chat_id: int) -> Optional[dict]:
        return self.active_streams.get(chat_id)
