from pydantic import BaseModel
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from bson import ObjectId

from typing import Optional, List, Dict, Any, Type, TypeVar

import logging


logger = logging.getLogger('mangodm_logger')
logging.basicConfig(filename='mangodm.log',
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')


class DataBase:
    client: AsyncIOMotorClient  # type: ignore
    db: AsyncIOMotorDatabase  # type: ignore


db: DataBase = DataBase()

"""
COLLECTIONS["{collection_name}"] = {Model}
"""
COLLECTIONS: Dict[str, Type["Document"]] = {}
EMBEDDED_COLLECTIONS: Dict[str, Type["EmbeddedDocument"]] = {}


async def connect_to_mongo(MONGODB_URL: str, MONGODB: str):
    db.client = AsyncIOMotorClient(f"{MONGODB_URL}")
    db.db = db.client[MONGODB]
    
    logger.info("connect to mongo")


def close_mongo_connection():
    db.client.close()
        
    logger.info("close mongo connection")


T = TypeVar('T', bound='Document')
EmbdT = TypeVar('EmbdT', bound='EmbeddedDocument')


class EmbeddedDocument(BaseModel):
    @classmethod
    def register_embedded_collection(cls):
        EMBEDDED_COLLECTIONS[cls.__name__] = cls

    def to_document(self) -> Dict[str, Any]:
        model_dict: Dict[str, Any] = dict(self)
        document: Dict[str, Any] = {
            "_type": "embedded_document",
            "_embedded_document": self.__class__.__name__
        }

        for key, value in model_dict.items():
            if isinstance(value, Document):
                if not value.is_saved():
                    logger.error("Subdocument not saved")
                    raise Exception("Subdocument not saved")
                document[key] = value.to_subdocument()
            elif isinstance(value, EmbeddedDocument):
                document[key] = value.to_document()
            else:
                document[key] = value

        return document

    def to_response(self) -> Dict[str, Any]:
        model_dict: Dict[str, Any] = dict(self)
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
    async def document_to_model(cls: Type[EmbdT], document: Dict[str, Any]) -> EmbdT:
        for key, value in document.items():
            if isinstance(value, dict):
                if '_type' not in value:
                    continue
                if value['_type'] == 'subdocument':
                    document[key] = await Document.from_subdocument(value)
                elif value['_type'] == 'embedded_document':
                    document[key] = await EmbeddedDocument.from_subembedded(value)

        return cls(**document)

    @classmethod
    async def from_subembedded(cls, subdocument: Dict[str, Any]):
        if subdocument['_type'] != 'embedded_document':
            logger.error("Invalid subdocument")
            raise Exception("Invalid subdocument")
        if not subdocument['_embedded_document'] in EMBEDDED_COLLECTIONS:
            logger.error("Invalid subdocument")
            raise Exception("Invalid subdocument")

        del subdocument['_type']

        embedded_document_name = subdocument['_embedded_document']
        del subdocument['_embedded_document']

        submodel = await EMBEDDED_COLLECTIONS[embedded_document_name] \
            .document_to_model(subdocument)
        return submodel


class Document(BaseModel):
    id: str = "-1"

    class Config:
        collection_name: str = "default"
        excludeFields: List[str] = []
        excludeFieldsResponse: List[str] = []

    @classmethod
    def register_collection(cls):
        if not 'collection_name' in cls.Config.__dict__:
            cls.Config.collection_name = cls.__name__
        COLLECTIONS[cls.Config.collection_name] = cls

    def is_saved(self) -> bool:
        return self.id != "-1"

    def to_document(self, for_create=False) -> Dict[str, Any]:
        if for_create:
            if self.is_saved():
                logger.error("Document already created")
                raise Exception("Document already created")
        else:
            if not self.is_saved():
                logger.error("Document not saved")
                raise Exception("Document not saved")

        model_dict: Dict[str, Any] = dict(self)
        document: Dict[str, Any] = dict()
        if not for_create:
            document['_id'] = ObjectId(model_dict['id'])
        del model_dict['id']

        if 'excludeFields' in self.Config.__dict__:
            for field in self.Config.excludeFields:
                del model_dict[field]
        for key, value in model_dict.items():
            if isinstance(value, Document):
                if not value.is_saved():
                    logger.error("Subdocument not saved")
                    raise Exception("Subdocument not saved")
                document[key] = value.to_subdocument()
            elif isinstance(value, EmbeddedDocument):
                document[key] = value.to_document()
            else:
                document[key] = value

        return document

    def to_response(self) -> Dict[str, Any]:
        if not self.is_saved():
            logger.error("Document not saved")
            raise Exception("Document not saved")

        model_dict: Dict[str, Any] = dict(self)
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

    def to_subdocument(self) -> Dict[str, Any]:
        if not self.is_saved():
            logger.error("Document not saved")
            raise Exception("Document not saved")

        document: Dict[str, Any] = {
            "_type": "subdocument",
            "_collection": self.Config.collection_name,
            "_id": self.id
        }

        return document

    @classmethod
    async def from_subdocument(cls, subdocument: Dict[str, Any]):
        if subdocument["_type"] != "subdocument":
            logger.error("Invalid subdocument")
            raise Exception("Invalid subdocument")
        model = await COLLECTIONS[subdocument['_collection']].get(
            id=subdocument["_id"])

        return model

    @classmethod
    async def document_to_model(cls: Type[T], document: Dict[str, Any]) -> T:
        document['id'] = str(document['_id'])
        del document['_id']
        for key, value in document.items():
            if isinstance(value, dict):
                if '_type' not in value:
                    continue
                if value['_type'] == 'subdocument':
                    document[key] = await Document.from_subdocument(value)
                elif value['_type'] == 'embedded_document':
                    document[key] = await EmbeddedDocument.from_subembedded(value)

        return cls(**document)

    @classmethod
    async def get(cls: Type[T], **kwargs) -> Optional[T]:
        if "id" in kwargs:
            kwargs['_id'] = ObjectId(kwargs['id'])
            del kwargs["id"]

        document = await db.db[cls.Config.collection_name].find_one(kwargs)
        if document:
            return await cls.document_to_model(document)
        return None

    @classmethod
    async def find(cls: Type[T], **kwargs) -> List[T]:
        if "id" in kwargs:
            kwargs['_id'] = ObjectId(kwargs['id'])
            del kwargs["id"]

        cursor = db.db[cls.Config.collection_name].find(kwargs)
        models: List[T] = []
        async for document in cursor:
            models.append(await cls.document_to_model(document))

        return models

    async def create(self):
        new_document = self.to_document(for_create=True)
        result = await db.db[self.Config.collection_name].insert_one(new_document)
        self.id = str(result.inserted_id)

    async def update(self, recursive_update=False):
        document = self.to_document()
        if not self.is_saved():
            logger.error("Document not saved")
            raise Exception("Document not saved")
        if recursive_update:
            for value in dict(self).values():
                if isinstance(value, Document):
                    await value.update(recursive_update=True)

        await db.db[self.Config.collection_name].update_one(
            {'_id': ObjectId(self.id)}, {'$set': document})

    async def delete(self):
        if not self.is_saved():
            logger.error("Document not saved")
            raise Exception("Document not saved")
        await db.db[self.Config.collection_name].delete_one(
            {'_id': ObjectId(self.id)})
