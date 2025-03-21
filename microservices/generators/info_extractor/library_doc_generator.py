from kafka import KafkaConsumer
import json
import logging

from info_extractor.utils.environment import (
    KAFKA_TOPIC,
    KAFKA_HOST,
    KAFKA_PORT,
    KAFKA_CONSUMER_GROUP,
)

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)


def library_doc_generator():
    # Create Kafka consumer
    consumer = KafkaConsumer(
        KAFKA_TOPIC,
        bootstrap_servers=[f"{KAFKA_HOST}:{KAFKA_PORT}"],
        auto_offset_reset="earliest",
        enable_auto_commit=True,
        group_id=KAFKA_CONSUMER_GROUP,
        value_deserializer=lambda x: json.loads(x.decode("utf-8")),
        key_deserializer=lambda x: x.decode("utf-8") if x else None,
    )

    logging.info("Consumer 2 started. Waiting for messages...")

    # Process messages
    for message in consumer:
        message_data = message.value
        message_id = message_data["id"]
        message_value = message_data["file_key"]

        logging.info(f"Consumed by consumer 2: ID={message_id}, Value={message_value}")
