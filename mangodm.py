from pydantic import BaseModel
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase


class DataBase:
    client: AsyncIOMotorClient  # type: ignore
    db: AsyncIOMotorDatabase  # type: ignore

    def __init__(self, connect_url, database_name) -> None:
        self.client = AsyncIOMotorClient(connect_url)
        self.db = self.client[database_name]

    def close_connection(self) -> None:
        self.client.close()
