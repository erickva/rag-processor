"""
Base interfaces for delivery providers.

Defines the contract for uploading chunks to vector databases
with embeddings and metadata.
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
import numpy as np

from ..utils.text_utils import ChunkMetadata


@dataclass
class DeliveryResult:
    """Result of a delivery operation."""
    
    success: bool
    chunks_uploaded: int
    errors: List[str]
    provider: str
    destination: str
    metadata: Dict[str, Any]


class EmbeddingProvider(ABC):
    """Base class for embedding generation providers."""
    
    @abstractmethod
    def generate_embedding(self, text: str) -> np.ndarray:
        """Generate embedding vector for text."""
        pass
    
    @abstractmethod  
    def generate_embeddings(self, texts: List[str]) -> List[np.ndarray]:
        """Generate embeddings for multiple texts (batch)."""
        pass
    
    @property
    @abstractmethod
    def dimension(self) -> int:
        """Embedding vector dimension."""
        pass


class DeliveryProvider(ABC):
    """Base class for vector database delivery providers."""
    
    def __init__(self, embedding_provider: EmbeddingProvider):
        """Initialize with embedding provider."""
        self.embedding_provider = embedding_provider
    
    @property
    @abstractmethod
    def name(self) -> str:
        """Provider name (e.g., 'supabase', 'pinecone')."""
        pass
    
    @abstractmethod
    def connect(self, **kwargs) -> bool:
        """Establish connection to vector database."""
        pass
    
    @abstractmethod
    def upload_chunks(
        self, 
        chunks: List[ChunkMetadata], 
        table_name: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> DeliveryResult:
        """
        Upload chunks with embeddings to vector database.
        
        Args:
            chunks: List of text chunks with metadata
            table_name: Database table/collection name
            metadata: Additional metadata to attach to all chunks
            
        Returns:
            DeliveryResult with upload status and statistics
        """
        pass
    
    @abstractmethod
    def test_connection(self) -> bool:
        """Test if connection is working."""
        pass
    
    def prepare_chunk_data(
        self, 
        chunks: List[ChunkMetadata],
        additional_metadata: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        Prepare chunks for upload by generating embeddings and formatting data.
        
        Args:
            chunks: List of text chunks
            additional_metadata: Extra metadata to add to each chunk
            
        Returns:
            List of formatted chunk data ready for database insertion
        """
        # Extract texts for batch embedding
        texts = [chunk.text for chunk in chunks]
        
        # Generate embeddings in batch for efficiency
        embeddings = self.embedding_provider.generate_embeddings(texts)
        
        prepared_chunks = []
        for i, chunk in enumerate(chunks):
            chunk_data = {
                "text": chunk.text,
                "embedding": embeddings[i].tolist(),  # Convert numpy to list for JSON
                "metadata": chunk.metadata.copy(),
                "start_position": chunk.start_position,
                "end_position": chunk.end_position,
            }
            
            # Add additional metadata if provided
            if additional_metadata:
                chunk_data["metadata"].update(additional_metadata)
            
            prepared_chunks.append(chunk_data)
        
        return prepared_chunks