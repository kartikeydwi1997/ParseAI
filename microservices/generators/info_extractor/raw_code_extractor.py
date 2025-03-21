import json
import logging
from kafka import KafkaConsumer
import ast
from pydantic import BaseModel
import os

from info_extractor.utils.environment import (
    KAFKA_HOST,
    KAFKA_PORT,
    KAFKA_TOPIC,
    KAFKA_CONSUMER_GROUP,
)
from info_extractor.utils.environment import get_env
from info_extractor.utils.storage import StorageConfig, StorageService
from info_extractor.utils.mongo_store import MongoDBClient, MongoCollections
from info_extractor.utils.consumer_processing import post_consumption_processing

# Set up logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)


def strip_docstrings(source_code: str):
    # Parse the source code into an AST
    tree = ast.parse(source_code)

    # Remove all docstrings
    def remove_docstrings(node):
        if isinstance(
            node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef, ast.Module)
        ):
            if (
                node.body
                and isinstance(node.body[0], ast.Expr)
                and isinstance(node.body[0].value, ast.Constant)
                and isinstance(node.body[0].value.value, str)
            ):
                node.body.pop(0)
        for child in ast.iter_child_nodes(node):
            remove_docstrings(child)

    remove_docstrings(tree)

    # Get the transformed code
    cleaned_code = ast.unparse(tree)

    return cleaned_code


class FileKey(BaseModel):
    id: str
    file_key: str
    hash: str


def value_deserializer(v: str) -> FileKey:
    return FileKey(**json.loads(v.decode("utf-8")))


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


def raw_code_extractor():
    # Create Kafka consumer
    consumer = KafkaConsumer(
        KAFKA_TOPIC,
        bootstrap_servers=[f"{KAFKA_HOST}:{KAFKA_PORT}"],
        auto_offset_reset="earliest",
        enable_auto_commit=True,
        group_id=KAFKA_CONSUMER_GROUP,
        value_deserializer=value_deserializer,
        key_deserializer=lambda x: x.decode("utf-8") if x else None,
    )

    logging.info("Raw code extraction consumer started. Waiting for messages...")

    storage = get_storage_service()
    mongo_client = MongoDBClient()

    for message in consumer:
        message_data = message.value
        project_id = message_data.id
        file_key = message_data.file_key
        file_hash = message_data.hash

        raw_code_extraction_result = "Error"
        try:
            body = storage.get_file(key=file_key).get("Body", None)
            if body is None:
                raise ValueError(f"Failed to fetch key: {file_key}")
            file_contents = body.read().decode("utf-8")
            body.close()

            cleaned_file_contents = strip_docstrings(source_code=file_contents)

            file_basename, file_ext = os.path.basename(file_key).rsplit(".", 1)
            file_dirname = os.path.dirname(file_key)
            updated_file_key = os.path.join(
                file_dirname, f"{file_basename}_rawCodeExtracted.{file_ext}"
            )
            storage.upload_file(
                file_content=cleaned_file_contents, file_path=updated_file_key
            )
            raw_code_extraction_result = updated_file_key

            logging.info(
                f"Consumed by raw code extractor: id={project_id}, file_key={file_key}, hash={file_hash}"
            )
        except Exception as e:
            logging.error(
                f"Error in consuming message, id={project_id}, file_key={file_key}, hash={file_hash}, error: {e}"
            )
        finally:
            mongo_client.update(
                collection_name=MongoCollections.FileProcessing.value,
                document={
                    "$set": {
                        f"fileProcessingStatus.{file_hash}.rawCodeExtraction": raw_code_extraction_result
                    }
                },
                condition={
                    "projectId": project_id,
                },
            )

            post_consumption_processing(
                project_id=project_id, mongo_client=mongo_client
            )
