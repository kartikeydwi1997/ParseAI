from pymilvus import MilvusClient, DataType
from pydantic import BaseModel, field_serializer
from enum import Enum
from typing import List
import numpy as np

from processing_api.utils.environment import (
    MILVUS_HOST,
    MILVUS_EMBEDDING_SIZE,
    MILVUS_COLLECTION,
)
from processing_api.utils.singleton import singleton


SEARCH_LIMIT = 10


class VectorType(Enum):
    DocString = "DocString"
    LibraryDocString = "LibraryDocString"
    RawCode = "RawCode"
    FileSummary = "FileSummary"

    def to_file_processing_key(self) -> str:
        match self:
            case VectorType.DocString:
                return "docstringGeneration"
            case VectorType.LibraryDocString:
                return "libraryDocGeneration"
            case VectorType.RawCode:
                return "rawCodeExtraction"
            case VectorType.FileSummary:
                return "promptFile"


class RelatedDocuments(BaseModel):
    vec_type: VectorType
    file_hash: str

    @field_serializer("vec_type")
    def serialize_vec_type(self, vec_type: VectorType) -> str:
        return vec_type.value


class QueryDocument(BaseModel):
    project_id: str
    vector: List[float]


@singleton
class MilvusDBClient:
    def __init__(self):
        self.__client = MilvusClient(uri=MILVUS_HOST)

        index_params = self.__client.prepare_index_params()
        index_params.add_index(field_name="vector", metric_type="L2")
        index_params.add_index(
            field_name="vec_type", index_type="Trie", index_name="my_trie_1"
        )
        index_params.add_index(
            field_name="file_hash", index_type="Trie", index_name="my_trie_2"
        )
        index_params.add_index(
            field_name="project_id", index_type="Trie", index_name="my_trie_3"
        )

        self.__client.create_index(
            collection_name=MILVUS_COLLECTION, index_params=index_params
        )

    def search(self, query_document: QueryDocument) -> List[RelatedDocuments]:
        self.__client.load_collection(MILVUS_COLLECTION)
        matches = self.__client.search(
            collection_name=MILVUS_COLLECTION,
            data=np.expand_dims(np.array(query_document.vector), axis=0),
            limit=SEARCH_LIMIT,
            filter=f"project_id == '{query_document.project_id}'",
            output_fields=["file_hash", "vec_type"],
        )

        result = []
        for match in matches[0]:
            entity = match.get("entity", None)
            if entity is None:
                continue

            result.append(
                RelatedDocuments(
                    vec_type=entity["vec_type"],
                    file_hash=entity["file_hash"],
                )
            )

        return result
