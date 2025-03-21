from kafka import KafkaConsumer
import json
import logging
import ast
from typing import Dict, List, Optional, Any
from pydantic import BaseModel
import os

from info_extractor.utils.environment import (
    KAFKA_PORT,
    KAFKA_HOST,
    KAFKA_TOPIC,
    KAFKA_CONSUMER_GROUP,
)
from info_extractor.utils.storage import StorageService, StorageConfig
from info_extractor.utils.environment import get_env
from info_extractor.utils.mongo_store import MongoDBClient, MongoCollections
from info_extractor.utils.consumer_processing import post_consumption_processing


logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)


def extract_docstrings(file_contents: str) -> Dict[str, Any]:
    """
    Extract all docstrings from a Python file and return them in a structured format.

    Args:
        file_contents: Contents of a file

    Returns:
        A dictionary containing the structured docstrings with the following format:
        {
            "module_docstring": "module level docstring",
            "classes": [
                {
                    "name": "ClassName",
                    "docstring": "class docstring",
                    "methods": [
                        {
                            "name": "method_name",
                            "docstring": "method docstring"
                        }
                    ]
                }
            ],
            "functions": [
                {
                    "name": "function_name",
                    "docstring": "function docstring"
                }
            ]
        }
    """
    result = {"module_docstring": None, "classes": [], "functions": []}

    # Parse the Python file into an AST
    tree = ast.parse(file_contents)

    # Extract module docstring
    if ast.get_docstring(tree):
        result["module_docstring"] = ast.get_docstring(tree)

    # First, process all top-level nodes to handle classes and functions
    for node in ast.iter_child_nodes(tree):
        # Handle top-level function definitions
        if isinstance(node, ast.FunctionDef):
            func_info = {
                "name": node.name,
                "docstring": ast.get_docstring(node),
                "args": _extract_function_args(node),
            }
            result["functions"].append(func_info)

        # Handle class definitions
        elif isinstance(node, ast.ClassDef):
            class_info = {
                "name": node.name,
                "docstring": ast.get_docstring(node),
                "methods": [],
            }

            # Extract methods from the class
            for child_node in ast.iter_child_nodes(node):
                if isinstance(child_node, ast.FunctionDef):
                    method_info = {
                        "name": child_node.name,
                        "docstring": ast.get_docstring(child_node),
                        "args": _extract_function_args(child_node),
                    }
                    class_info["methods"].append(method_info)

            result["classes"].append(class_info)

    return result


def _extract_function_args(node: ast.FunctionDef) -> List[Dict[str, str]]:
    """
    Extract function arguments and their annotations.

    Args:
        node: The AST node representing a function definition

    Returns:
        A list of dictionaries containing argument names and their type annotations
    """
    args = []

    for arg in node.args.args:
        arg_info = {
            "name": arg.arg,
            "annotation": _annotation_to_string(arg.annotation),
        }
        args.append(arg_info)

    return args


def _annotation_to_string(annotation: Optional[ast.expr]) -> Optional[str]:
    """
    Convert a type annotation AST node to a string representation.

    Args:
        annotation: The AST node representing a type annotation

    Returns:
        String representation of the annotation or None if no annotation is present
    """
    if annotation is None:
        return None

    try:
        return ast.unparse(annotation)
    except AttributeError:
        # For Python < 3.9, ast.unparse is not available
        return "annotation_present"


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


def doc_string_generator():
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

    logging.info("Doc string generation consumer started. Waiting for messages...")

    storage = get_storage_service()
    mongo_client = MongoDBClient()

    for message in consumer:
        message_data = message.value
        project_id = message_data.id
        file_key = message_data.file_key
        file_hash = message_data.hash

        doc_string_generation_result = "Error"
        try:
            body = storage.get_file(key=file_key).get("Body", None)
            if body is None:
                raise ValueError(f"Failed to fetch key: {file_key}")
            file_contents = body.read().decode("utf-8")
            body.close()

            result = extract_docstrings(file_contents=file_contents)

            file_basename = os.path.basename(file_key).rsplit(".", 1)[0]
            file_dirname = os.path.dirname(file_key)
            updated_file_key = os.path.join(
                file_dirname, f"{file_basename}_docStringGenerated.json"
            )
            storage.upload_file(
                file_content=json.dumps(result, indent=4), file_path=updated_file_key
            )
            doc_string_generation_result = updated_file_key

            logging.info(
                f"Consumed by doc string generator: id={project_id}, file_key={file_key}, hash={file_hash}"
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
                        f"fileProcessingStatus.{file_hash}.docstringGeneration": doc_string_generation_result
                    }
                },
                condition={
                    "projectId": project_id,
                },
            )

            post_consumption_processing(
                project_id=project_id, mongo_client=mongo_client
            )
