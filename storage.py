import database as db


class Database:
    async def initialize(self):
        await db.initialize()

    async def close(self):
        await db.close()

    async def save_content(
        self,
        content_id,
        source,
        title,
        content_type=None,
        metadata=None,
    ):
        metadata = metadata or {}

        await db.save_content(
            content_id=content_id,
            source=source,
            title=title,
            content_type=content_type,
            description=metadata.get("description"),
            metadata=metadata,
        )

    async def save_playback(
        self,
        chat_id,
        content_id,
        position=0,
        status="idle",
        metadata=None,
    ):
        metadata = metadata or {}

        await db.save_playback(
            chat_id=chat_id,
            content_id=content_id,
            status=status,
            position_seconds=position,
            source=metadata.get("source"),
        )


database = Database()


async def initialize_storage():
    await database.initialize()


async def close_storage():
    await database.close()


def get_database():
    return database
