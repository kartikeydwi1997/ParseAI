from kafka import KafkaProducer
from kafka.producer.future import FutureRecordMetadata
import os
from pydantic import BaseModel

from processing_api.utils.singleton import singleton


def value_serializer_fn(v: BaseModel):
    return v.model_dump_json().encode("utf-8")


class FileMessage(BaseModel):
    id: str
    file_key: str
    hash: str


@singleton
class FileProducer:
    SEND_MESSAGE_TIMEOUT = 3

    def __init__(self):
        kafka_host = os.environ.get("KAFKA_HOST", None)
        kafka_port = os.environ.get("KAFKA_PORT", None)
        kafka_topic = os.environ.get("KAFKA_TOPIC", None)

        if kafka_host is None or kafka_port is None or kafka_topic is None:
            raise ValueError("Set KAFKA_HOST, KAFKA_PORT, and KAFKA_TOPIC")

        self.__producer = KafkaProducer(
            bootstrap_servers=[f"{kafka_host}:{kafka_port}"],
            value_serializer=value_serializer_fn,
            key_serializer=lambda k: k.encode("utf-8"),
        )
        self.__topic = kafka_topic

    def send_message(self, message: FileMessage) -> bool:
        try:
            future: FutureRecordMetadata = self.__producer.send(
                self.__topic,
                key=message.id,
                value=message,
            )
            future.get(timeout=self.SEND_MESSAGE_TIMEOUT)
            return True
        except:
            return False
