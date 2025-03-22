from pymilvus import MilvusClient, DataType
from pydantic import BaseModel, field_serializer
from enum import Enum
from typing import List
import numpy as np

from file_vectorizer.utils.environment import (
    MILVUS_HOST,
    MILVUS_EMBEDDING_SIZE,
    MILVUS_COLLECTION,
)
from file_vectorizer.utils.singleton import singleton


class VectorType(Enum):
    DocString = "DocString"
    LibraryDocString = "LibraryDocString"
    RawCode = "RawCode"
    FileSummary = "FileSummary"


class CodeVectorDocument(BaseModel):
    vec_type: VectorType
    project_id: str
    file_hash: str
    vector: List[float]

    @field_serializer("vector")
    def serialize_vector(self, vector: List[float]):
        return np.array(vector)

    @field_serializer("vec_type")
    def serialize_vec_type(self, vec_type: VectorType):
        return vec_type.value


@singleton
class MilvusDBClient:
    def __init__(self):
        self.__client = MilvusClient(uri=MILVUS_HOST)

        self.__client.create_collection(
            collection_name=MILVUS_COLLECTION,
            dimension=MILVUS_EMBEDDING_SIZE,
            auto_id=True,
        )

    def upsert(self, code_vector_document: CodeVectorDocument) -> None:
        data_dict = code_vector_document.model_dump()

        self.__client.upsert(
            collection_name=MILVUS_COLLECTION,
            data=[data_dict],
        )
