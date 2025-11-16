import google.generativeai as genai
from typing import List
import numpy as np
from config import settings
import logging

logger = logging.getLogger(__name__)


class EmbeddingService:
    def __init__(self):
        self.api_key = settings.GEMINI_API_KEY
        self.model_name = settings.EMBEDDING_MODEL
        self.dimension = settings.EMBEDDING_DIMENSION
        self.disabled = not bool(self.api_key)
        if not self.disabled:
            genai.configure(api_key=self.api_key)
            logger.info(f"Initialized EmbeddingService with model: {self.model_name}")
        else:
            logger.warning(
                "GEMINI_API_KEY not set. Embeddings will fall back to zero vectors "
                f"(dim={self.dimension}). You can still ingest and search by keyword, "
                "but vector search quality will be disabled."
            )
    
    async def generate_embedding(self, text: str) -> List[float]:
        """Generate embedding for a single text"""
        try:
            if self.disabled:
                return [0.0] * self.dimension
            result = genai.embed_content(
                model=self.model_name,
                content=text,
                task_type="retrieval_document"
            )
            return result['embedding']
        except Exception as e:
            logger.error(f"Error generating embedding: {e}")
            raise
    
    async def generate_embeddings_batch(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for multiple texts"""
        if self.disabled:
            return [[0.0] * self.dimension for _ in texts]
        embeddings = []
        for text in texts:
            embedding = await self.generate_embedding(text)
            embeddings.append(embedding)
        return embeddings
    
    async def generate_query_embedding(self, query: str) -> List[float]:
        """Generate embedding for a query"""
        try:
            result = genai.embed_content(
                model=self.model_name,
                content=query,
                task_type="retrieval_query"
            )
            return result['embedding']
        except Exception as e:
            logger.error(f"Error generating query embedding: {e}")
            raise


embedding_service = EmbeddingService()