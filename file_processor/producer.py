from random import choice
from confluent_kafka import Producer


def main():
    config = {
        "bootstrap.servers": "prod-3.ghar:9092",
        "acks": "all",
    }

    producer = Producer(config)

    def delivery_callback(err, msg):
        if err:
            print(f"ERROR: Message failed delivery: {err}")
        else:
            print(
                f"Produced event to topic {msg.topic()}: key = {msg.key().decode('utf-8')} value = {msg.value().decode('utf-8')}"
            )

    topic = "test-topic"
    user_ids = ["eabara", "jsmith", "sgarcia", "jbernard", "htanaka", "awalther"]
    products = ["book", "alarm clock", "t-shirts", "gift card", "batteries"]

    count = 0
    for _ in range(10):
        user_id = choice(user_ids)
        product = choice(products)
        producer.produce(topic, product, user_id, callback=delivery_callback)
        count += 1

    producer.poll(10000)
    producer.flush()


if __name__ == "__main__":
    main()
