from kafka import KafkaConsumer
import json
import logging
import ast
import importlib
import inspect
from typing import Dict, Optional
from pydantic import BaseModel
import os

from info_extractor.utils.environment import (
    KAFKA_TOPIC,
    KAFKA_HOST,
    KAFKA_PORT,
    KAFKA_CONSUMER_GROUP,
)
from info_extractor.utils.environment import get_env
from info_extractor.utils.storage import StorageConfig, StorageService
from info_extractor.utils.mongo_store import MongoDBClient, MongoCollections
from info_extractor.utils.consumer_processing import post_consumption_processing

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)


def get_library_docstrings(script_content: str) -> Dict[str, Dict[str, Optional[str]]]:
    """
    Analyzes a Python script and returns a dictionary containing all imported
    library functions and classes along with their docstrings.

    Args:
        script_content (str): The content of the Python script to analyze

    Returns:
        Dict[str, Dict[str, Optional[str]]]: A dictionary where:
            - Keys are module names
            - Values are dictionaries mapping function/class names to their docstrings
    """
    # Parse the script content into an AST
    tree = ast.parse(script_content)

    # Dictionary to store imported modules
    imported_modules = {}

    # Dictionary to store results
    results = {}

    # Find all import statements
    for node in ast.walk(tree):
        # Handle regular imports (import x, import x.y)
        if isinstance(node, ast.Import):
            for alias in node.names:
                module_name = alias.name
                asname = alias.asname or module_name
                imported_modules[asname] = module_name

        # Handle from imports (from x import y, from x.y import z)
        elif isinstance(node, ast.ImportFrom):
            module_name = node.module
            for alias in node.names:
                name = alias.name
                asname = alias.asname or name

                if module_name:
                    full_name = f"{module_name}.{name}"
                else:  # relative import
                    full_name = name

                imported_modules[asname] = full_name

    # Find all function and class calls
    used_items = set()

    for node in ast.walk(tree):
        # Check for function/method calls
        if isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name):
                # Direct function call (func())
                func_name = node.func.id
                if func_name in imported_modules:
                    used_items.add(imported_modules[func_name])

            elif isinstance(node.func, ast.Attribute):
                # Method or module.function call (obj.method() or module.func())
                if isinstance(node.func.value, ast.Name):
                    module_name = node.func.value.id
                    if module_name in imported_modules:
                        # It's a module.function call
                        full_name = f"{imported_modules[module_name]}.{node.func.attr}"
                        used_items.add(full_name)

        # Check for class instantiations
        elif isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
            class_name = node.func.id
            if class_name in imported_modules:
                used_items.add(imported_modules[class_name])

    # Get docstrings for each used item
    for item_path in used_items:
        parts = item_path.split(".")

        try:
            # Try to import the module
            if len(parts) == 1:
                # It's just a module
                module = importlib.import_module(parts[0])
                module_name = parts[0]
                item_name = parts[0]
                item = module
            else:
                # It's a module.something
                module_name = parts[0]
                module = importlib.import_module(module_name)

                # Navigate to the specific item
                item = module
                for part in parts[1:]:
                    try:
                        item = getattr(item, part)
                    except AttributeError:
                        # Try to import a submodule
                        submodule_name = f"{module_name}.{part}"
                        try:
                            item = importlib.import_module(submodule_name)
                            module_name = submodule_name
                        except ImportError:
                            item = None
                            break

                item_name = parts[-1]

            if item:
                # Get docstring
                docstring = inspect.getdoc(item)

                # Add to results
                if module_name not in results:
                    results[module_name] = {}

                results[module_name][item_name] = docstring

                # If it's a module, get all public functions and classes
                if len(parts) == 1:
                    for attr_name in dir(item):
                        if not attr_name.startswith("_"):  # Public attributes only
                            attr = getattr(item, attr_name)
                            if inspect.isfunction(attr) or inspect.isclass(attr):
                                attr_docstring = inspect.getdoc(attr)
                                results[module_name][attr_name] = attr_docstring

        except (ImportError, AttributeError):
            # Module or attribute not found, possibly a local or built-in function
            pass

    return results


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


def library_doc_generator():
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

    logging.info(
        "Library docstring generation consumer started. Waiting for messages..."
    )

    storage = get_storage_service()
    mongo_client = MongoDBClient()

    for message in consumer:
        message_data = message.value
        project_id = message_data.id
        file_key = message_data.file_key
        file_hash = message_data.hash

        library_doc_generation_result = "Error"
        try:
            body = storage.get_file(key=file_key).get("Body", None)
            if body is None:
                raise ValueError(f"Failed to fetch key: {file_key}")
            file_contents = body.read().decode("utf-8")
            body.close()

            library_docstrings = get_library_docstrings(script_content=file_contents)

            file_basename, file_ext = os.path.basename(file_key).rsplit(".", 1)
            file_dirname = os.path.dirname(file_key)
            updated_file_key = os.path.join(
                file_dirname, f"{file_basename}_libraryDocStringGenerated.json"
            )
            storage.upload_file(
                file_content=json.dumps(library_docstrings, indent=4),
                file_path=updated_file_key,
            )
            library_doc_generation_result = updated_file_key

            logging.info(
                f"Consumed by library doc string generator: id={project_id}, file_key={file_key}, hash={file_hash}"
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
                        f"fileProcessingStatus.{file_hash}.libraryDocGeneration": library_doc_generation_result
                    }
                },
                condition={
                    "projectId": project_id,
                },
            )

            post_consumption_processing(
                project_id=project_id, mongo_client=mongo_client
            )
