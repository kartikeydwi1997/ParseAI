import os


def get_env(key: str):
    value = os.environ.get(key, None)
    if value is None:
        raise ValueError(f"Environment variable '{key}' not set!")

    return value


RABBIT_HOST = get_env("RABBIT_HOST")
RABBIT_PORT = get_env("RABBIT_PORT")
RABBIT_QUEUE = get_env("RABBIT_QUEUE")

GEMINI_MODEL = get_env("GEMINI_MODEL")
GEMINI_EMBED_MODEL = get_env("GEMINI_EMBED_MODEL")
GEMINI_API_KEY = get_env("GEMINI_API_KEY")
