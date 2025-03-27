from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from enum import Enum
from typing import List
import logging

from processing_api.utils.mongo_store import MongoDBClient, MongoCollections
from processing_api.utils.milvus_store import MilvusDBClient, QueryDocument
from processing_api.utils.llm import GeminiAPIDao
from processing_api.utils.environment import get_env
from processing_api.utils.storage import StorageConfig, StorageService


logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)


app = FastAPI()


class Role(Enum):
    User = "user"
    Assistant = "assistant"


class Message(BaseModel):
    role: Role
    content: str


class QueryRequest(BaseModel):
    project_id: str
    messages: List[Message]


def get_storage_service():
    endpoint_host = get_env("STORAGE_HOST")
    endpoint_port = get_env("STORAGE_PORT")

    config = StorageConfig(
        endpoint_url=f"http://{endpoint_host}:{endpoint_port}",
        access_key=get_env("STORAGE_ACCESS_KEY"),
        secret_key=get_env("STORAGE_SECRET_KEY"),
        bucket_name=get_env("STORAGE_BUCKET_NAME"),
    )
    return StorageService(config)


@app.post("/query/", response_model=dict)
async def process_query(request: QueryRequest):
    mongo_client = MongoDBClient()
    project = mongo_client.get_by_id(
        collection_name=MongoCollections.FileProcessing.value,
        condition={"projectId": str(request.project_id)},
    )

    if not project:
        raise HTTPException(
            status_code=404, detail=f"Project not found: {request.project_id}"
        )

    if len(request.messages) > 30:
        raise HTTPException(status_code=400, detail=f"Max context allowed: 30")

    vector_db = MilvusDBClient()
    llm = GeminiAPIDao()

    last_message = request.messages[-1].content
    embedding = llm.get_embeddings(message=last_message)
    s3 = get_storage_service()

    result_documents = vector_db.search(
        query_document=QueryDocument(
            project_id=request.project_id,
            vector=embedding,
        )
    )

    file_processing_status = project.get("fileProcessingStatus", {})
    project_context = []
    for result_document in result_documents:
        file_key_name = result_document.vec_type.to_file_processing_key()
        file_key = file_processing_status.get(result_document.file_hash, {}).get(
            file_key_name, ""
        )
        if file_key == "":
            continue

        logging.info(f"Prompt file key = {file_key}")

        file_content = s3.get_file(key=file_key)["Body"].read()
        project_context.append(f"<CONTEXT>{file_content}</CONTEXT>")
    project_context_str = "\n".join(project_context)

    converstion_context = "\n".join(
        [
            f"Role:{message.role.value}\nContent:{message.content}"
            for message in request.messages
        ]
    )

    prompt = f"""
<SYSTEM-INSTRUCTION>

</SYSTEM-INSTRUCTION>

You are given this context:

<CONVERSATION-CONTEXT>
{converstion_context}
</CONVERSATION-CONTEXT>

And also some information from the project:

<PROJECT-CONTEXT>
{project_context_str}
</PROJECT-CONTEXT>
    """

    model_output = llm.prompt(message=prompt)

    return {"message": model_output, "context": prompt, "role": Role.Assistant.value}


@app.get("/health")
async def health_check():
    return {"status": "ok"}
