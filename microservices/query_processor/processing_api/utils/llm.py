import google.generativeai as genai
from typing import Optional, List
import numpy as np
from numpy.linalg import norm
import logging


from processing_api.utils.singleton import singleton
from processing_api.utils.environment import (
    GEMINI_MODEL,
    GEMINI_EMBED_MODEL,
    GEMINI_API_KEY,
)


@singleton
class GeminiAPIDao:
    def __init__(self) -> None:
        genai.configure(api_key=GEMINI_API_KEY)
        self.__model = genai.GenerativeModel(model_name=GEMINI_MODEL)

    def prompt(self, message: str) -> Optional[str]:
        message_formatted = {"role": "user", "parts": [message]}

        try:
            response = self.__model.generate_content(message_formatted)
            return response.text
        except Exception as e:
            logging.error(f"Failed to generate content: {e}")
            return None

    def get_embeddings(self, message: str) -> List[float]:
        try:
            response = genai.embed_content(
                model=GEMINI_EMBED_MODEL,
                content=message,
                task_type="SEMANTIC_SIMILARITY",
            )
            return response["embedding"]
        except Exception as e:
            logging.error(f"Failed to generate embeddings: {e}")
            return []
