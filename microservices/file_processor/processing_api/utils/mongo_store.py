from pymongo import MongoClient
from bson import ObjectId
import os
from typing import Dict, Any, Optional
from enum import Enum

from processing_api.utils.singleton import singleton


class MongoCollections(Enum):
    FileProcessing = "FileProcessing"


@singleton
class MongoDBClient:
    def __init__(self):
        mongo_host = os.environ.get("MONGO_HOST")
        mongo_port = os.environ.get("MONGO_PORT")

        if not mongo_host or not mongo_port:
            raise ValueError(
                "MONGO_HOST and MONGO_PORT environment variables must be set"
            )

        self.client = MongoClient(f"mongodb://{mongo_host}:{mongo_port}")
        self.db = self.client["parse-ai"]

    def put(self, collection_name: str, document: Dict[str, Any]) -> str:
        """
        Insert a document into the specified collection

        Args:
            collection_name: Name of the collection
            document: Document to insert

        Returns:
            The ID of the inserted document as a string
        """
        collection = self.db[collection_name]
        result = collection.insert_one(document)
        return str(result.inserted_id)

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
