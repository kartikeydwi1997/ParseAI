from confluent_kafka import Consumer


def main():
    config = {
        "bootstrap.servers": "192.168.1.127:9092",
        "group.id": "kafka-python-getting-started",
        "auto.offset.reset": "earliest",
    }

    consumer = Consumer(config)

    topic = "test-topic"
    consumer.subscribe([topic])

    try:
        while True:
            msg = consumer.poll(1.0)
            if msg is None:
                print("Waiting...")
            elif msg.error():
                print(f"Error: {msg.error()}")
            else:
                print(
                    f"Consumed event from topic {msg.topic()}: key = {msg.key().decode('utf-8')} value = {msg.value().decode('utf-8')}"
                )
    except KeyboardInterrupt:
        pass
    finally:
        consumer.close()


if __name__ == "__main__":
    main()
