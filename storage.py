from database import Database
from config import settings


database = Database(settings.database_url)


async def initialize_storage():
    await database.initialize()


async def close_storage():
    await database.close()


def get_database() -> Database:
    return database
