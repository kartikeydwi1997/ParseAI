import os


def get_env(key: str):
    value = os.environ.get(key, None)
    if value is None:
        raise ValueError(f"Environment variable '{key}' not set!")

    return value


KAFKA_HOST = get_env("KAFKA_HOST")
KAFKA_PORT = get_env("KAFKA_PORT")
KAFKA_TOPIC = get_env("KAFKA_TOPIC")
KAFKA_CONSUMER_GROUP = get_env("KAFKA_CONSUMER_GROUP")
