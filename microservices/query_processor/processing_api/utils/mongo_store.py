from enum import Enum
from pymongo import MongoClient
import os
from typing import Dict, Optional, Any

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
