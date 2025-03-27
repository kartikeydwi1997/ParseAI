import os


def get_env(key: str):
    value = os.environ.get(key, None)
    if value is None:
        raise ValueError(f"Environment variable '{key}' not set!")

    return value


GEMINI_MODEL = get_env("GEMINI_MODEL")
GEMINI_EMBED_MODEL = get_env("GEMINI_EMBED_MODEL")
GEMINI_API_KEY = get_env("GEMINI_API_KEY")

MILVUS_HOST = get_env("MILVUS_HOST")
MILVUS_EMBEDDING_SIZE = int(get_env("MILVUS_EMBEDDING_SIZE"))
MILVUS_COLLECTION = get_env("MILVUS_COLLECTION")
