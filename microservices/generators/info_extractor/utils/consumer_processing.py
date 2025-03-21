import logging
from pydantic import BaseModel

from info_extractor.utils.mongo_store import MongoCollections, MongoDBClient
from info_extractor.utils.queue import publish_message


class ProjectPromptGenerationMessage(BaseModel):
    project_id: str


def post_consumption_processing(project_id: str, mongo_client: MongoDBClient):
    updated_document = mongo_client.get_by_id(
        collection_name=MongoCollections.FileProcessing.value,
        condition={
            "projectId": project_id,
        },
    )

    if updated_document is not None:
        file_processing_status = updated_document.get("fileProcessingStatus", {})

        completely_processed_count = 0
        for file_info in file_processing_status.values():
            if all([val != "" for val in file_info.values()]):
                completely_processed_count += 1

        if completely_processed_count == len(file_processing_status):
            logging.info("All processed, dumping to RabbitMQ")
            prompt_message = ProjectPromptGenerationMessage(project_id=project_id)
            publish_message(message=prompt_message)
        else:
            logging.info(
                f"Current processed count = [{completely_processed_count}/{len(file_processing_status)}]"
            )
