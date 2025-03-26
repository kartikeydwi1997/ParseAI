from enum import Enum
from processing_api.utils.singleton import Singleton
from pymongo import MongoClient

class MongoCollections(Enum):
    FileProcessing = "file_processing"
    QueryResults = "query_results"

class MongoDBClient(metaclass=Singleton):
    def __init__(self):
        mongo_host = os.environ.get("MONGO_HOST")
        mongo_port = os.environ.get("MONGO_PORT")

        if not mongo_host or not mongo_port:
            raise ValueError(
                "MONGO_HOST and MONGO_PORT environment variables must be set"
            )

        self.client = MongoClient(f"mongodb://{mongo_host}:{mongo_port}")
        self.db = self.client["parse-ai"]


    def get_by_id(self, collection_name: str, condition: dict):
        return self.db[collection_name].find_one(condition)