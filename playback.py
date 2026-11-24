from typing import Optional

from database import Database
from streaming import StreamingManager


class PlaybackManager:
    def __init__(
        self,
        database: Database,
        streaming: StreamingManager,
    ):
        self.database = database
        self.streaming = streaming
        self.sessions: dict[int, dict] = {}

    async def play(
        self,
        chat_id: int,
        content_id: str,
        media_url: str,
        title: str,
        video: bool = True,
    ):
        await self.streaming.play(
            chat_id=chat_id,
            media_url=media_url,
            video=video,
        )

        session = {
            "content_id": content_id,
            "title": title,
            "media_url": media_url,
            "video": video,
            "status": "playing",
        }

        self.sessions[chat_id] = session

        await self.database.save_playback(
            chat_id=chat_id,
            content_id=content_id,
            position=0,
            status="playing",
            metadata=session,
        )

        return session

    async def stop(self, chat_id: int):
        await self.streaming.stop(chat_id)

        session = self.sessions.get(chat_id)
        if session:
            session["status"] = "stopped"

            await self.database.save_playback(
                chat_id=chat_id,
                content_id=session["content_id"],
                position=0,
                status="stopped",
                metadata=session,
            )

    async def resume(self, chat_id: int) -> Optional[dict]:
        session = self.sessions.get(chat_id)

        if not session or not session.get("media_url"):
            return None

        await self.streaming.play(
            chat_id=chat_id,
            media_url=session["media_url"],
            video=session.get("video", True),
        )

        session["status"] = "playing"
        return session

    def get_session(self, chat_id: int) -> Optional[dict]:
        return self.sessions.get(chat_id)
