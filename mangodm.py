from pydantic import BaseModel
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from bson import ObjectId

from typing import Optional, List, Dict, Any

import logging


MONGODB_URL = ""
MONGODB = ""

logger = logging.getLogger('mangodm_logger')
logging.basicConfig(filename='mangodm.log',
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')


class DataBase:
    client: AsyncIOMotorClient  # type: ignore
    db: AsyncIOMotorDatabase  # type: ignore

    def __init__(self, connect_url, database_name) -> None:
        self.client = AsyncIOMotorClient(connect_url)
        self.db = self.client[database_name]

    async def connect_to_mongo(self):
        db.client = AsyncIOMotorClient(f"{MONGODB_URL}")
        db.db = db.client[MONGODB]

    def close_connection(self) -> None:
        self.client.close()


db: DataBase


class EmbeddedDocument(BaseModel):
    def to_document(self) -> Dict[str, Any]:
        model_dict: Dict[str, Any] = self.model_dump()
        document: Dict[str, Any] = {}

        for key, value in model_dict.items():
            if isinstance(value, Document):
                if not value.is_saved():
                    logger.error("Subdocument not saved")
                    raise Exception("Subdocument not saved")
                document[key] = value.id
            elif isinstance(value, EmbeddedDocument):
                document[key] = value.to_document()
            else:
                document[key] = value

        return document

    def to_response(self) -> Dict[str, Any]:
        model_dict: Dict[str, Any] = self.model_dump()
        response: Dict[str, Any] = {}

        for key, value in model_dict.items():
            if isinstance(value, Document):
                response[key] = value.to_response()
            elif isinstance(value, EmbeddedDocument):
                response[key] = value.to_response()
            else:
                response[key] = value

        return response

    @classmethod
    def document_to_model(cls, document: Dict[str, Any]) -> "EmbeddedDocument":
        for key, value in document.items():
            if isinstance(value, ObjectId):
                document[key] = Document.get(id=value)
            elif isinstance(value, dict):
                document[key] = cls.document_to_model(value)

        return cls(**document)


class Document(BaseModel):
    id: str = "-1"

    class Config:
        collection_name: str = "default"
        excludeFields: List[str] = []
        excludeFieldsResponse: List[str] = []

    @classmethod
    def get_fields(cls) -> Dict[str, Any]:
        properties = cls.model_json_schema().get("properties")
        if properties:
            return properties
        else:
            logging.error("No fields found")
            raise Exception("No fields found")

    def is_saved(self) -> bool:
        return self.id != "-1"

    def to_document(self) -> Dict[str, Any]:
        if not self.is_saved():
            logger.error("Document not saved")
            raise Exception("Document not saved")

        model_dict: Dict[str, Any] = self.model_dump()
        document: Dict[str, Any] = {
            '_id': ObjectId(model_dict['id'])
        }
        del model_dict['id']

        if 'excludeFields' in self.Config.__dict__:
            for field in self.Config.excludeFields:
                del model_dict[field]

        for key, value in model_dict.items():
            if isinstance(value, Document):
                if not value.is_saved():
                    logger.error("Subdocument not saved")
                    raise Exception("Subdocument not saved")
                document[key] = value.id

            elif isinstance(value, EmbeddedDocument):
                document[key] = value.to_document()
            else:
                document[key] = value

        return document

    def to_response(self) -> Dict[str, Any]:
        if not self.is_saved():
            logger.error("Document not saved")
            raise Exception("Document not saved")

        model_dict: Dict[str, Any] = self.model_dump()
        response: Dict[str, Any] = {}

        if 'excludeFieldsResponse' in self.Config.__dict__:
            for field in self.Config.excludeFieldsResponse:
                del model_dict[field]

        for key, value in model_dict.items():
            if isinstance(value, Document):
                response[key] = value.to_response()
            elif isinstance(value, EmbeddedDocument):
                response[key] = value.to_response()
            else:
                response[key] = value

        return response

    @classmethod
    def document_to_model(cls, document: Dict[str, Any]) -> "Document":
        for key, value in document.items():
            if key == '_id':
                document['id'] = str(value)
                del document['_id']
            if isinstance(value, ObjectId):
                document[key] = Document.get(id=value)
            elif isinstance(value, dict):
                document[key] = cls.document_to_model(value)

        return cls(**document)

    @classmethod
    async def get(cls, **kwargs) -> Optional["Document"]:
        if "id" in kwargs:
            kwargs['_id'] = ObjectId(kwargs['id'])
            del kwargs["id"]

        document = await db.db[cls.Config.collection_name].find_one(kwargs)
        if document:
            return cls.document_to_model(document)
        return None

    @classmethod
    async def find(cls, **kwargs) -> List["Document"]:
        if "id" in kwargs:
            kwargs['_id'] = ObjectId(kwargs['id'])
            del kwargs["id"]

        cursor = db.db[cls.Config.collection_name].find(kwargs)
        models: List["Document"] = []
        async for document in cursor:
            models.append(cls.document_to_model(document))

        return models

    async def create(self):
        new_document = self.to_document()
        result = await db.db[self.Config.collection_name].insert_one(new_document)
        self.id = str(result.inserted_id)

    async def update(self):
        document = self.to_document()
        if not self.is_saved():
            logger.error("Document not saved")
            raise Exception("Document not saved")
        await db.db[self.Config.collection_name].update_one(
            {'_id': ObjectId(self.id)}, {'$set': document})

    async def delete(self):
        if not self.is_saved():
            logger.error("Document not saved")
            raise Exception("Document not saved")
        await db.db[self.Config.collection_name].delete_one(
            {'_id': ObjectId(self.id)})
