import os


def get_env(key: str):
    value = os.environ.get(key, None)
    if value is None:
        raise ValueError(f"Environment variable '{key}' not set!")

    return value


RABBIT_HOST = get_env("RABBIT_HOST")
RABBIT_PORT = get_env("RABBIT_PORT")
RABBIT_QUEUE = get_env("RABBIT_QUEUE")
