import logging
from typing import List
from sentence_transformers import SentenceTransformer
from backend.config import settings

logger = logging.getLogger(__name__)

class EmbeddingService:
    """Embedding generation service using HuggingFace SentenceTransformers."""

    def __init__(self, model_name: str = None):
        self.model_name = model_name or settings.EMBEDDING_MODEL_NAME
        logger.info(f"Initializing SentenceTransformer model: {self.model_name}")
        self._model = None

    @property
    def model(self) -> SentenceTransformer:
        if self._model is None:
            logger.info(f"Loading SentenceTransformer model instance for '{self.model_name}'...")
            self._model = SentenceTransformer(self.model_name)
        return self._model

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """Generate dense vector embeddings for a list of document strings."""
        if not texts:
            return []
        embeddings = self.model.encode(texts, show_progress_bar=False, convert_to_numpy=True)
        return embeddings.tolist()

    def embed_query(self, text: str) -> List[float]:
        """Generate dense vector embedding for a single search query string."""
        if not text or not text.strip():
            return []
        embedding = self.model.encode(text, show_progress_bar=False, convert_to_numpy=True)
        return embedding.tolist()

embedding_service = EmbeddingService()
