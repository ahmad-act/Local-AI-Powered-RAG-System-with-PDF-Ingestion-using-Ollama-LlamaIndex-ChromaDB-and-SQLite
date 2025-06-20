# rag_system/embedding/ollama_embedder.py
import logging
from src.config.app_settings import AppSettings
import requests
from typing import List
from llama_index.core.base.embeddings.base import BaseEmbedding
from pydantic import Field
import logging
from src.config.logging_config import setup_logging

setup_logging()
logger = logging.getLogger(__name__)

class OllamaEmbedding(BaseEmbedding):
    model: str = Field(default=AppSettings.EMBED_MODEL, description="Ollama embedding model name")
    url: str = Field(default=f"{AppSettings.OLLAMA_BASE_URL}/api/embeddings", description="Ollama embeddings API endpoint")

    def __init__(self, model: str = AppSettings.EMBED_MODEL):
        super().__init__(model_name=model)

    def _get_query_embedding(self, query: str) -> List[float]:
        try:
            response = requests.post(
                self.url,
                json={"model": self.model, "prompt": query},
                timeout=10
            )
            response.raise_for_status()
            embedding = response.json().get("embedding")
            if embedding is None:
                raise ValueError("No embedding in response")
            return embedding
        except Exception as e:
            logger.exception("Embedding failed for query")
            raise RuntimeError(f"Failed to get embedding: {str(e)}") from e

    def _get_text_embedding(self, text: str) -> List[float]:
        return self._get_query_embedding(text)

    async def _aget_query_embedding(self, query: str) -> List[float]:
        raise NotImplementedError("Async embedding not supported")

    def _get_text_embeddings(self, texts: List[str]) -> List[List[float]]:
        try:
            return [self._get_query_embedding(text) for text in texts]
        except Exception as e:
            logger.exception("Batch embedding failed")
            raise RuntimeError(f"Failed to get batch embeddings: {str(e)}") from e
