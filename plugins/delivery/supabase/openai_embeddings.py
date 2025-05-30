"""
OpenAI embedding provider.

Generates embeddings using OpenAI's text-embedding models.
"""

import os
from typing import List, Optional
import numpy as np

try:
    import openai
    HAS_OPENAI = True
except ImportError:
    HAS_OPENAI = False

from .base import EmbeddingProvider
from config.constants import DEFAULT_EMBEDDING_MODEL, OPENAI_EMBEDDING_DIMENSIONS, ERROR_MISSING_API_KEY


class OpenAIEmbeddingProvider(EmbeddingProvider):
    """OpenAI embedding provider using text-embedding-ada-002 or newer models."""
    
    def __init__(self, model: str = DEFAULT_EMBEDDING_MODEL, api_key: Optional[str] = None):
        """
        Initialize OpenAI embedding provider.
        
        Args:
            model: OpenAI embedding model name
            api_key: OpenAI API key (if not provided, reads from OPENAI_API_KEY env var)
        """
        if not HAS_OPENAI:
            raise ImportError("openai package required. Install with: pip install openai")
        
        self.model = model
        self.client = openai.OpenAI(api_key=api_key or os.getenv("OPENAI_API_KEY"))
        
        # Validate API key
        if not self.client.api_key:
            raise ValueError(ERROR_MISSING_API_KEY.format(env_var="OPENAI_API_KEY"))
    
    def generate_embedding(self, text: str) -> np.ndarray:
        """Generate embedding for single text."""
        try:
            response = self.client.embeddings.create(
                model=self.model,
                input=text
            )
            return np.array(response.data[0].embedding)
        except Exception as e:
            raise RuntimeError(f"Failed to generate embedding: {e}")
    
    def generate_embeddings(self, texts: List[str]) -> List[np.ndarray]:
        """Generate embeddings for multiple texts in batch."""
        if not texts:
            return []
        
        try:
            response = self.client.embeddings.create(
                model=self.model,
                input=texts
            )
            return [np.array(data.embedding) for data in response.data]
        except Exception as e:
            raise RuntimeError(f"Failed to generate batch embeddings: {e}")
    
    @property
    def dimension(self) -> int:
        """Embedding dimension for the model."""
        return OPENAI_EMBEDDING_DIMENSIONS.get(self.model, 1536)  # Default to ada-002 dimension