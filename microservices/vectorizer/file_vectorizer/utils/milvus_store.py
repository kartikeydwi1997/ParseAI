from pymilvus import MilvusClient, DataType
from pydantic import BaseModel, field_serializer
from enum import Enum
from typing import List
import numpy as np
import uuid

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
        self.__id = 0

        schema = self.__client.create_schema(enable_dynamic_field=True)
        schema.add_field("id", DataType.INT64, is_primary=True)
        schema.add_field("vector", DataType.FLOAT_VECTOR, dim=MILVUS_EMBEDDING_SIZE)
        schema.add_field("vec_type", DataType.VARCHAR, max_length=64)
        schema.add_field("file_hash", DataType.VARCHAR, max_length=128)
        schema.add_field("project_id", DataType.VARCHAR, max_length=128)

        self.__client.create_collection(
            collection_name=MILVUS_COLLECTION,
            dimension=MILVUS_EMBEDDING_SIZE,
            schema=schema,
            consistency_level="Strong",
        )

    def __increment_id(self):
        self.__id += 1

    def insert(self, code_vector_document: CodeVectorDocument) -> None:
        data_dict = code_vector_document.model_dump()
        self.__increment_id()
        data_dict["id"] = self.__id

        self.__client.insert(
            collection_name=MILVUS_COLLECTION,
            data=[data_dict],
        )
