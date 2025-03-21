from pymongo import MongoClient
from typing import Dict, Any, Optional
from enum import Enum

from info_extractor.utils.singleton import singleton
from info_extractor.utils.environment import get_env


class MongoCollections(Enum):
    FileProcessing = "FileProcessing"


@singleton
class MongoDBClient:
    def __init__(self):
        mongo_host = get_env("MONGO_HOST")
        mongo_port = get_env("MONGO_PORT")

        if not mongo_host or not mongo_port:
            raise ValueError(
                "MONGO_HOST and MONGO_PORT environment variables must be set"
            )

        self.client = MongoClient(f"mongodb://{mongo_host}:{mongo_port}")
        self.db = self.client["parse-ai"]

    def update(
        self, collection_name: str, document: Dict[str, Any], condition: Dict[str, Any]
    ) -> int:
        """
        Insert a document into the specified collection

        Args:
            collection_name: Name of the collection
            document: Document to insert

        Returns:
            The ID of the inserted document as a string
        """
        collection = self.db[collection_name]
        result = collection.update_one(filter=condition, update=document)
        return result.modified_count

    def get_by_id(
        self, collection_name: str, condition: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        try:
            collection = self.db[collection_name]
            document = collection.find_one(condition, {"_id": 0})
            return document
        except Exception as e:
            print(f"Error retrieving document: {e}")
            return None
