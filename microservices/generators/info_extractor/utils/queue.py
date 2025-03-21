from pydantic import BaseModel
import pika
import logging

from info_extractor.utils.environment import RABBIT_HOST, RABBIT_PORT, RABBIT_QUEUE


RABBIT_CONNECTION_ATTEMPTS = 3
RABBIT_CONNECTION_DELAY = 2


def publish_message(message: BaseModel) -> bool:
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
        logging.error(f"Failed to connect to RabbitMQ: {e}")
        return

    channel = connection.channel()

    channel.queue_declare(queue=RABBIT_QUEUE, durable=True)

    try:
        channel.basic_publish(
            exchange="",
            routing_key=RABBIT_QUEUE,
            body=message.model_dump_json(),
            properties=pika.BasicProperties(delivery_mode=pika.DeliveryMode.Persistent),
        )
    except Exception as e:
        logging.error(f"Failed to publish message: {e}")
        return False

    connection.close()
