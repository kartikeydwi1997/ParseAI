import pika
from pika.adapters.blocking_connection import BlockingChannel
import logging
import json
import os

from file_vectorizer.utils.environment import (
    RABBIT_HOST,
    RABBIT_PORT,
    RABBIT_QUEUE,
    get_env,
)
from file_vectorizer.utils.storage import StorageConfig, StorageService
from file_vectorizer.utils.mongo_store import MongoCollections, MongoDBClient
from file_vectorizer.utils.model import QueueMessage, FileProcessingStatus
from file_vectorizer.utils.llm import GeminiAPIDao


logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)

RABBIT_CONNECTION_ATTEMPTS = 3
RABBIT_CONNECTION_DELAY = 3


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


class ProjectVectorizingConsumer:
    def __init__(self) -> None:
        self.__channel = self.__init_channel(queue_name=RABBIT_QUEUE)
        self.__storage = get_storage_service()
        self.__db_client = MongoDBClient()
        self.__llm = GeminiAPIDao()

    def start_listening(self) -> None:
        self.__channel.start_consuming()

    def stop_listening(self) -> None:
        self.__channel.stop_consuming()
        self.__channel.close()

    def __init_channel(self, queue_name: str) -> BlockingChannel:
        try:
            connection = pika.BlockingConnection(
                pika.ConnectionParameters(
                    host=RABBIT_HOST,
                    port=RABBIT_PORT,
                    connection_attempts=RABBIT_CONNECTION_ATTEMPTS,
                    retry_delay=RABBIT_CONNECTION_DELAY,
                )
            )
        except pika.exceptions.AMQPConnectionError as e:
            logging.info(f"Failed to connect to RabbitMQ: {e}")
            raise Exception(f"Failed to connect to RabbitMQ: {e}")

        channel = connection.channel()

        channel.queue_declare(queue=queue_name, durable=True)

        channel.basic_qos(prefetch_count=1)
        channel.basic_consume(
            queue=queue_name, on_message_callback=self.message_processor
        )

        return channel

    def __get_file_contents(self, key: str) -> str:
        if key == "Error":
            return ""

        body = self.__storage.get_file(key=key)
        return body.get("Body").read().decode("utf-8")

    def __generate_all_details_prompt(
        self, file_processing_status: FileProcessingStatus
    ) -> str:
        doc_string_file_contents = self.__get_file_contents(
            file_processing_status.docstringGeneration
        )
        library_doc_string_file_contents = self.__get_file_contents(
            file_processing_status.libraryDocGeneration
        )
        raw_code_file_contents = self.__get_file_contents(
            file_processing_status.rawCodeExtraction
        )

        prompt = f"""
You are a python expert. Your task is to generate a summary of a given python script.
I will give you the python code, all the docstrings in the python code and also 
the docstrings of all the library functions and classes used. 

The code will be in between <CODE></CODE> tags. 
The doc string information will be JSON formatted and in between <DOCSTRING></DOCSTRING> tags.
The library doc string information will be JSON formatted and in between <LIBDSTRING></LIBDSTRING> tags.

If any of the tags are empty, then it means I do not have that information to give you.

<CODE>
{raw_code_file_contents}
</CODE>

<DOCSTRING>
{doc_string_file_contents}
</DOCSTRING>

<LIBDSTRING>
{library_doc_string_file_contents}
</LIBDSTRING>
        """

        return prompt

    def message_processor(self, ch, method, _properties, body):
        logging.info(body.decode())

        try:
            message = QueueMessage(**json.loads(body.decode()))

            projectDetails = self.__db_client.get_by_id(
                collection_name=MongoCollections.FileProcessing.value,
                condition={"projectId": message.project_id},
            )

            if projectDetails is None:
                raise ValueError(f"No project with id: '{message.project_id}' found!")

            for file_info in projectDetails.get("fileProcessingStatus", {}).values():
                file_processing_status = FileProcessingStatus(**file_info)
                prompt = self.__generate_all_details_prompt(file_processing_status)

                file_key = file_processing_status.fileKey
                file_name = os.path.basename(file_key).rsplit(".", 1)[0]
                dirname = os.path.dirname(file_key)
                updated_file_key = os.path.join(dirname, f"{file_name}_prompt.txt")

                self.__storage.upload_file(
                    file_content=prompt,
                    file_path=updated_file_key,
                )

                model_result = self.__llm.prompt(message=prompt)
                embedding = self.__llm.get_embeddings(message=model_result)
                logging.info(f"key={file_key}, result={model_result}")

            logging.info(
                f"Number of files in project = {len(projectDetails.get('fileProcessingStatus', {}))}"
            )
        except Exception as e:
            logging.error(f"Error when processing message: {e}")
        finally:
            ch.basic_ack(delivery_tag=method.delivery_tag)


if __name__ == "__main__":
    consumer = None

    try:
        consumer = ProjectVectorizingConsumer()
        consumer.start_listening()
    except KeyboardInterrupt:
        logging.info("Shutting down project vectorizing consumer.")
    except Exception as e:
        logging.error("Error: {e}")
    finally:
        consumer.stop_listening()
